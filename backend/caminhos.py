"""Caminhos de teste viáveis e cenários de borda, calculados sobre configurações do modelo.

Uma configuração é o estado e os valores das variáveis de estado. O contexto é escolhido antes da busca e os
dados de entrada a cada evento, a partir dos candidatos de fronteira das guardas (`validacao.candidatos`). A
escolha corre em camadas sobre a combinação de valores numéricos do caminho: só positivos, depois com zero,
depois todos; a camada seguinte só é usada quando a anterior não torna a transição viável. Um valor de contexto
declarado no modelo (`valor_inicial`) é tentado antes dos demais. Os eventos seguem a semântica de `simulador`:
vale a primeira transição declarada cuja guarda é verdadeira.
"""
import ast
import itertools
import math
from collections import deque
from dataclasses import dataclass
from datetime import date, timedelta
from types import SimpleNamespace

from . import expressoes, simulador
from .expressoes import NUMERICOS, ErroExpressao
from .schemas import estado_inicial, estados_finais
from .validacao import DATA_BASE, candidatos

TRANSICOES = "transicoes"
ELEMENTARES = "elementares"
ESTRATEGIAS = {TRANSICOES: "Todas as transições", ELEMENTARES: "Caminhos elementares"}

CAMADAS = (0, 1, 2)  # só positivos; positivos e zero; todos
LIMITE_DADOS = 1000  # combinações de dados de entrada tentadas por evento
LIMITE_SONDAGENS = 200  # pontos de disparo examinados por comparação, nos cenários de borda

MOTIVO_PROFUNDIDADE = "profundidade máxima atingida"
MOTIVO_CONTEXTO = "limite de combinações de contexto atingido"
MOTIVO_ORIGEM = "o estado de origem não é alcançado com os valores candidatos"
MOTIVO_GUARDA = "nenhum valor candidato satisfaz a guarda"
MOTIVO_FINAL = "não há caminho viável até um estado final depois da transição"
MOTIVO_ELEMENTAR = "nenhum caminho elementar viável passa pela transição"
MOTIVO_SEM_DENTRO = "nenhum valor junto da fronteira satisfaz a guarda"
MOTIVO_SEM_CAMINHO = "os valores da fronteira não formam um caminho viável"

ERROS_DE_AVALIACAO = (ErroExpressao, KeyError, TypeError, ArithmeticError, ValueError)
_INVALIDA = object()  # guarda fora da linguagem: a transição nunca dispara
_FALHA = object()  # as ações da transição não puderam ser executadas

_SIMBOLOS = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">="}
_ESPELHO = {"<=": ">=", "<": ">", ">=": "<=", ">": "<", "==": "==", "!=": "!="}
_INVERSO = {"<=": ">", "<": ">=", ">=": "<", ">": "<=", "==": "!=", "!=": "=="}
_PADRAO = {"inteiro": [0, 1], "decimal": [0, 1], "booleano": [False, True], "data": [DATA_BASE]}


@dataclass(frozen=True)
class Limites:
    profundidade: int = 30
    caminhos: int = 200
    combinacoes_contexto: int = 50
    passos_borda: int = 10_000


@dataclass(frozen=True)
class Passo:
    """Um evento do caminho: dados de entrada, transição que o aceitou (None se recusado) e estado depois dele."""

    evento: str
    dados: tuple[tuple[str, object], ...]
    transicao: int | None
    estado: str

    @property
    def aceito(self) -> bool:
        return self.transicao is not None


@dataclass(frozen=True)
class Caminho:
    """Sequência de eventos a partir do estado inicial, com os valores de contexto do cenário."""

    inicial: str
    contexto: tuple[tuple[str, object], ...]
    passos: tuple[Passo, ...]
    borda: bool = False

    @property
    def final(self) -> str:
        return self.passos[-1].estado if self.passos else self.inicial

    def indices(self) -> list[int]:
        return [p.transicao for p in self.passos if p.transicao is not None]

    def estados(self) -> list[str]:
        return [self.inicial, *(p.estado for p in self.passos)]

    def criterios(self, modelo: dict) -> list[int]:
        return sorted({n for i in self.indices() for n in modelo["transicoes"][i].get("criterios") or []})


@dataclass(frozen=True)
class Pendencia:
    item: str
    motivo: str


@dataclass(frozen=True)
class ResultadoCaminhos:
    caminhos: tuple[Caminho, ...]
    transicoes_pendentes: tuple[tuple[int, str], ...] = ()
    bordas_omitidas: tuple[Pendencia, ...] = ()
    avisos: tuple[str, ...] = ()


def gerar_caminhos(
    modelo: dict, estrategia: str = TRANSICOES, bordas: bool = True, limites: Limites | None = None
) -> ResultadoCaminhos:
    """Caminhos viáveis do modelo pela estratégia escolhida e, se pedido, os cenários de borda."""
    if estrategia not in ESTRATEGIAS:
        raise ValueError(f"Estratégia desconhecida: {estrategia}. Use {' ou '.join(ESTRATEGIAS)}.")
    busca = _Busca(modelo, limites or Limites())
    if estrategia == TRANSICOES:
        caminhos, pendentes = busca.todas_as_transicoes()
    else:
        caminhos, pendentes = busca.elementares()
    omitidas: list[Pendencia] = []
    if bordas:
        extras, omitidas = busca.bordas(caminhos)
        caminhos = [*caminhos, *extras]
    return ResultadoCaminhos(tuple(caminhos), tuple(pendentes), tuple(omitidas), tuple(busca.avisos))


# ---------------------------------------------------------------- valores
def formatar_valor(valor) -> str:
    """Texto de um valor no cenário: verdadeiro/falso, números sem zeros sobrando e datas AAAA-MM-DD."""
    if isinstance(valor, bool):
        return "verdadeiro" if valor else "falso"
    if isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() and abs(valor) < 1e15 else repr(valor)
    return str(valor)


def _na_camada(valor, tipo: str, camada: int) -> bool:
    if tipo not in NUMERICOS or camada == 2:
        return True
    return valor > 0 if camada == 0 else valor >= 0


def _deslocar(valor, k: int, tipo: str):
    """Valor `k` passos além de `valor` (1, 0,01 ou 1 dia, conforme o tipo)."""
    if tipo == "data":
        dia = valor if isinstance(valor, date) else date.fromisoformat(valor)
        return (dia + timedelta(days=k)).isoformat()
    if tipo == "inteiro":
        return valor + k
    return round(valor + k * 0.01, 2)


def _inicios(operador: str, p, tipo: str):
    """(início dentro, sentido para dentro, início fora, sentido para fora); sentido 0 é um ponto único.

    "Dentro" é onde `variável operador p` é verdadeira, e os sentidos se afastam da fronteira.
    """
    if tipo == "booleano":
        if not isinstance(p, bool) or operador not in ("==", "!="):
            return None
        dentro = p if operador == "==" else not p
        return dentro, 0, not dentro, 0
    if tipo == "data":
        if isinstance(p, date):
            p = p.isoformat()
        if not isinstance(p, str):
            return None
    elif isinstance(p, bool) or not isinstance(p, (int, float)):
        return None
    elif tipo == "inteiro" and not float(p).is_integer():
        return None
    elif tipo == "inteiro":
        p = int(p)

    def um(k):
        return _deslocar(p, k, tipo)

    return {
        "<=": (p, -1, um(1), 1),
        "<": (um(-1), -1, p, 1),
        ">=": (p, 1, um(-1), -1),
        ">": (um(1), 1, p, -1),
        "==": (p, 0, um(1), 1),
        "!=": (um(1), 1, p, 0),
    }[operador]


def _sequencia(inicio, sentido: int, tipo: str, n: int):
    if sentido == 0:
        yield inicio
        return
    for k in range(n):
        yield _deslocar(inicio, sentido * k, tipo)


# ---------------------------------------------------------------- comparações e átomos das guardas
@dataclass(frozen=True)
class _Comparacao:
    no: ast.Compare
    variavel: str
    operador: str  # com a variável à esquerda, já considerando os "não" acima da comparação
    outro: ast.expr
    texto: str


def _literal(no: ast.expr) -> bool:
    if isinstance(no, ast.Constant):
        return isinstance(no.value, (bool, int, float, str))
    return (
        isinstance(no, ast.UnaryOp) and isinstance(no.op, ast.USub) and isinstance(no.operand, ast.Constant)
        and isinstance(no.operand.value, (int, float)) and not isinstance(no.operand.value, bool)
    )


def _como_comparacao(no: ast.Compare, negada: bool, variaveis: dict) -> _Comparacao | None:
    esquerda, direita = no.left, no.comparators[0]
    operador = _SIMBOLOS[type(no.ops[0])]

    def categoria(lado):
        if isinstance(lado, ast.Name) and lado.id in variaveis:
            return variaveis[lado.id]["categoria"]
        return "literal" if _literal(lado) else None

    ce, cd = categoria(esquerda), categoria(direita)
    if ce is None or cd is None or ce == cd == "literal":
        return None
    # Varia o lado cuja fronteira já se conhece quando o valor é escolhido: entrada, contexto, estado
    if ce == "entrada":
        lado = "esquerda"
    elif cd == "entrada":
        lado = "direita"
    elif ce == "contexto" and cd in ("contexto", "literal"):
        lado = "esquerda"
    elif cd == "contexto" and ce == "literal":
        lado = "direita"
    elif ce == "estado":
        lado = "esquerda"
    elif cd == "estado":
        lado = "direita"
    else:
        return None
    if lado == "direita":
        esquerda, direita, operador = direita, esquerda, _ESPELHO[operador]
    if negada:
        operador = _INVERSO[operador]
    return _Comparacao(no, esquerda.id, operador, direita, ast.unparse(no))


def _comparacoes(arvore: ast.expr, variaveis: dict) -> list[_Comparacao]:
    """Comparações de uma variável com um valor ou com outra variável, na ordem em que aparecem."""
    encontradas = []

    def visitar(no, negada):
        if isinstance(no, ast.BoolOp):
            for valor in no.values:
                visitar(valor, negada)
        elif isinstance(no, ast.UnaryOp) and isinstance(no.op, ast.Not):
            visitar(no.operand, not negada)
        elif isinstance(no, ast.Compare) and len(no.ops) == 1:
            comparacao = _como_comparacao(no, negada, variaveis)
            if comparacao:
                encontradas.append(comparacao)

    visitar(arvore, False)
    return encontradas


def _atomos(arvore: ast.expr) -> list[ast.expr]:
    """Condições elementares da guarda (o que fica abaixo de `e`, `ou` e `não`)."""
    if isinstance(arvore, ast.BoolOp):
        return [a for valor in arvore.values for a in _atomos(valor)]
    if isinstance(arvore, ast.UnaryOp) and isinstance(arvore.op, ast.Not):
        return _atomos(arvore.operand)
    return [arvore]


def _esqueleto(arvore: ast.expr, valores: dict[int, bool]) -> bool:
    """Resultado da guarda a partir dos valores das condições elementares."""
    if isinstance(arvore, ast.BoolOp):
        resultados = [_esqueleto(v, valores) for v in arvore.values]
        return all(resultados) if isinstance(arvore.op, ast.And) else any(resultados)
    if isinstance(arvore, ast.UnaryOp) and isinstance(arvore.op, ast.Not):
        return not _esqueleto(arvore.operand, valores)
    return valores[id(arvore)]


def _decisiva(arvore: ast.expr, no: ast.expr, valores: dict[int, bool]) -> bool:
    """A guarda é verdadeira e deixa de ser se só a condição `no` mudar."""
    if not _esqueleto(arvore, valores):
        return False
    return not _esqueleto(arvore, {**valores, id(no): not valores[id(no)]})


# ---------------------------------------------------------------- busca
class _Busca:
    def __init__(self, modelo: dict, limites: Limites):
        self.modelo = modelo
        self.limites = limites
        self.transicoes = modelo["transicoes"]
        self.inicial = estado_inicial(modelo)
        self.finais = set(estados_finais(modelo))
        self.variaveis = {v["nome"]: v for v in modelo.get("variaveis", [])}
        self.de_estado = [n for n, v in self.variaveis.items() if v["categoria"] == "estado"]
        self.avisos: list[str] = []
        self.arvores = [self._analisar(t) for t in self.transicoes]
        usadas_por = [self._usadas_na_guarda(i) | self._usadas_nas_acoes(i) for i in range(len(self.transicoes))]
        usadas = set().union(*usadas_por)
        self.de_contexto = [n for n, v in self.variaveis.items() if v["categoria"] == "contexto" and n in usadas]
        self.saidas: dict[str, list[int]] = {}
        self.do_par: dict[tuple[str, str], list[int]] = {}
        for i, t in enumerate(self.transicoes):
            self.saidas.setdefault(t["de"], []).append(i)
            self.do_par.setdefault((t["de"], t["evento"]), []).append(i)
        entradas = [n for n, v in self.variaveis.items() if v["categoria"] == "entrada"]
        self.entradas_do_par = {
            par: [n for n in entradas if any(n in usadas_por[i] for i in indices)]
            for par, indices in self.do_par.items()
        }
        self.acao_usa_entrada = [bool(self._usadas_nas_acoes(i) & set(entradas)) for i in range(len(self.transicoes))]
        self.candidatos = self._candidatos()
        self.camadas = self._camadas_distintas()
        self.inicio = (self.inicial, tuple(self.variaveis[n].get("valor_inicial") for n in self.de_estado))
        self.cortou_profundidade = False
        self.cortou_contexto = False
        self._movimentos_cache: dict = {}
        self._dados_cache: dict = {}

    # ---- leitura do modelo
    def _avisar(self, texto: str) -> None:
        if texto not in self.avisos:
            self.avisos.append(texto)

    def _analisar(self, transicao: dict):
        guarda = transicao.get("guarda")
        if not guarda:
            return None
        try:
            return simulador.arvore_da_guarda(guarda)
        except ErroExpressao as e:
            self._avisar(f"A guarda de {transicao.get('id', '?')} não pôde ser lida: {e}")
            return _INVALIDA

    def _usadas_na_guarda(self, i: int) -> set[str]:
        arvore = self.arvores[i]
        return expressoes.variaveis_usadas(arvore) if isinstance(arvore, ast.AST) else set()

    def _usadas_nas_acoes(self, i: int) -> set[str]:
        usadas = set()
        for texto in self.transicoes[i].get("acoes") or []:
            try:
                acao = expressoes.analisar_acao(texto)
            except ErroExpressao:
                continue
            usadas |= {acao.alvo} | expressoes.variaveis_usadas(acao.expressao)
        return usadas

    def _candidatos(self) -> dict[str, list]:
        arvores = [a for a in self.arvores if isinstance(a, ast.AST)]
        objetos = {
            n: SimpleNamespace(tipo=v["tipo"], valor_inicial=v.get("valor_inicial")) for n, v in self.variaveis.items()
        }
        try:
            base = candidatos(arvores, objetos) if arvores else {}
        except ERROS_DE_AVALIACAO:
            base = {}
        return {
            n: base.get(n) or list(_PADRAO.get(v["tipo"], [0]))
            for n, v in self.variaveis.items() if v["categoria"] != "estado"
        }

    def _valores(self, nome: str, camada: int) -> list:
        """Candidatos da variável na camada, em ordem; um valor de contexto declarado vem primeiro."""
        variavel = self.variaveis[nome]
        lista = [v for v in self.candidatos[nome] if _na_camada(v, variavel["tipo"], camada)]
        declarado = variavel.get("valor_inicial") if variavel["categoria"] == "contexto" else None
        if declarado is not None:
            lista = [declarado, *(v for v in lista if v != declarado)]
        return lista

    def _camadas_distintas(self) -> list[int]:
        """Camadas que mudam algum candidato (num modelo sem números, uma só)."""
        vistas, camadas = set(), []
        for camada in CAMADAS:
            assinatura = tuple(tuple(self._valores(n, camada)) for n in self.candidatos)
            if assinatura not in vistas:
                vistas.add(assinatura)
                camadas.append(camada)
        return camadas

    # ---- valores do cenário
    def _contextos(self, camada: int, fixos: dict | None = None):
        fixos = fixos or {}
        livres = [n for n in self.de_contexto if n not in fixos]
        listas = [self._valores(n, camada) for n in livres]
        if math.prod(len(lista) for lista in listas) > self.limites.combinacoes_contexto:
            self.cortou_contexto = True  # vira motivo só se algo deixar de ser coberto
        for combinacao in itertools.islice(itertools.product(*listas), self.limites.combinacoes_contexto):
            valores = {**dict(zip(livres, combinacao)), **fixos}
            yield {n: valores[n] for n in self.de_contexto}

    def _dados(self, de: str, evento: str, camada: int) -> list[dict]:
        chave = (de, evento, camada)
        if chave not in self._dados_cache:
            nomes = self.entradas_do_par.get((de, evento), [])
            listas = [self._valores(n, camada) for n in nomes]
            self._dados_cache[chave] = [
                dict(zip(nomes, c)) for c in itertools.islice(itertools.product(*listas), LIMITE_DADOS)
            ]
        return self._dados_cache[chave]

    def _ambiente(self, config, contexto: dict, dados: dict) -> dict:
        return {**dict(zip(self.de_estado, config[1])), **contexto, **dados}

    # ---- semântica dos eventos
    def _habilitada(self, i: int, ambiente: dict) -> bool:
        arvore = self.arvores[i]
        if arvore is None:
            return True
        if arvore is _INVALIDA:
            return False
        try:
            return bool(expressoes.avaliar(arvore, ambiente))
        except ERROS_DE_AVALIACAO:
            return False

    def _disparar(self, config, contexto: dict, evento: str, dados: dict):
        """(índice da transição que aceita o evento ou None, configuração seguinte)."""
        ambiente = self._ambiente(config, contexto, dados)
        for i in self.do_par.get((config[0], evento), ()):
            if not self._habilitada(i, ambiente):
                continue
            try:
                novos = expressoes.executar_acoes(self.transicoes[i].get("acoes") or [], ambiente)
                return i, (self.transicoes[i]["para"], tuple(novos[n] for n in self.de_estado))
            except ERROS_DE_AVALIACAO as e:
                self._avisar(f"As ações de {self.transicoes[i].get('id', '?')} não puderam ser executadas: {e}")
                return _FALHA, config
        return None, config

    def _movimentos(self, config, contexto: dict, camada: int) -> list:
        """Eventos aceitos a partir da configuração: um por transição e configuração resultante, em ordem."""
        chave = (config, tuple(contexto.items()), camada)
        if chave in self._movimentos_cache:
            return self._movimentos_cache[chave]
        resultado, vistos = [], set()
        for i in self.saidas.get(config[0], ()):
            t = self.transicoes[i]
            for dados in self._dados(t["de"], t["evento"], camada):
                j, nova = self._disparar(config, contexto, t["evento"], dados)
                if j != i or (i, nova) in vistos:
                    continue
                vistos.add((i, nova))
                resultado.append((Passo(t["evento"], tuple(dados.items()), i, nova[0]), nova))
                if not self.acao_usa_entrada[i]:
                    break  # os demais dados levam à mesma configuração
        self._movimentos_cache[chave] = resultado
        return resultado

    def _largura(self, inicio, contexto: dict, camada: int, limite: int):
        """Configurações alcançáveis a partir de `inicio`, da mais próxima à mais distante, com os passos até elas."""
        fila = deque([(inicio, ())])
        vistos = {inicio}
        while fila:
            config, passos = fila.popleft()
            yield config, passos
            movimentos = self._movimentos(config, contexto, camada)
            if len(passos) >= limite:
                if any(nova not in vistos for _, nova in movimentos):
                    self.cortou_profundidade = True
                continue
            for passo, nova in movimentos:
                if nova not in vistos:
                    vistos.add(nova)
                    fila.append((nova, (*passos, passo)))

    def _ate_final(self, config, contexto: dict, camada: int, limite: int):
        """Passos do caminho mais curto até um estado final, ou None."""
        for c in [c for c in self.camadas if c >= camada]:
            for nova, passos in self._largura(config, contexto, c, limite):
                if nova[0] in self.finais:
                    return passos
        return None

    def _caminho(self, contexto: dict, passos, borda: bool = False) -> Caminho:
        return Caminho(self.inicial, tuple(contexto.items()), tuple(passos), borda)

    # ---- estratégia: todas as transições
    def cobrir(self, alvo: int) -> tuple[Caminho | None, str]:
        """Caminho mais curto que dispara a transição `alvo` e termina num estado final, ou o motivo."""
        t = self.transicoes[alvo]
        self.cortou_profundidade = self.cortou_contexto = False
        origem = guarda = False
        for camada in self.camadas:
            for contexto in self._contextos(camada):
                for config, passos in self._largura(self.inicio, contexto, camada, self.limites.profundidade - 1):
                    if config[0] != t["de"]:
                        continue
                    origem = True
                    for dados in self._dados(t["de"], t["evento"], camada):
                        j, nova = self._disparar(config, contexto, t["evento"], dados)
                        if j != alvo:
                            continue
                        guarda = True
                        resto = self._ate_final(nova, contexto, camada, self.limites.profundidade - len(passos) - 1)
                        if resto is not None:
                            passo = Passo(t["evento"], tuple(dados.items()), alvo, nova[0])
                            return self._caminho(contexto, (*passos, passo, *resto)), ""
        if self.cortou_profundidade:
            return None, MOTIVO_PROFUNDIDADE
        if self.cortou_contexto:
            return None, MOTIVO_CONTEXTO
        return None, MOTIVO_FINAL if guarda else MOTIVO_GUARDA if origem else MOTIVO_ORIGEM

    def todas_as_transicoes(self) -> tuple[list[Caminho], list[tuple[int, str]]]:
        cobertas: set[int] = set()
        caminhos, pendentes = [], []
        for i in range(len(self.transicoes)):
            if i in cobertas:
                continue
            caminho, motivo = self.cobrir(i)
            if caminho is None:
                pendentes.append((i, motivo))
                continue
            caminhos.append(caminho)
            cobertas.update(caminho.indices())
        return caminhos, pendentes

    # ---- estratégia: caminhos elementares
    def _em_profundidade(self, inicio, contexto: dict, camada: int, alvo: int, cortou: list):
        """Caminhos de exatamente `alvo` passos até um estado final, sem repetir configuração."""
        no_caminho, passos = {inicio}, []

        def visitar(config):
            if config[0] in self.finais:
                if len(passos) == alvo:
                    yield tuple(passos)
                return
            movimentos = self._movimentos(config, contexto, camada)
            if len(passos) == alvo:
                if any(nova not in no_caminho for _, nova in movimentos):
                    cortou[0] = True
                return
            for passo, nova in movimentos:
                if nova in no_caminho:
                    continue
                no_caminho.add(nova)
                passos.append(passo)
                yield from visitar(nova)
                passos.pop()
                no_caminho.discard(nova)

        yield from visitar(inicio)

    def elementares(self) -> tuple[list[Caminho], list[tuple[int, str]]]:
        """Busca em profundidade com aprofundamento iterativo: os caminhos mais curtos vêm primeiro."""
        caminhos, vistas = [], set()
        limite = self.limites.caminhos
        atingiu_limite = False
        for camada in self.camadas:
            for contexto in self._contextos(camada):
                for alvo in range(1, self.limites.profundidade + 1):
                    cortou = [False]
                    for passos in self._em_profundidade(self.inicio, contexto, camada, alvo, cortou):
                        assinatura = tuple(p.transicao for p in passos)
                        if assinatura in vistas:
                            continue
                        if len(caminhos) == limite:
                            atingiu_limite = True
                            break
                        vistas.add(assinatura)
                        caminhos.append(self._caminho(contexto, passos))
                    if atingiu_limite:
                        break
                    if not cortou[0]:
                        break
                    if alvo == self.limites.profundidade:
                        self.cortou_profundidade = True
                if atingiu_limite:
                    break
            if atingiu_limite:
                break
        if atingiu_limite:
            self._avisar(f"Limite de {limite} caminhos atingido: há mais caminhos elementares do que os listados.")
        cobertas = {i for c in caminhos for i in c.indices()}
        if atingiu_limite:
            motivo = f"limite de {limite} caminhos atingido"
        elif self.cortou_profundidade:
            motivo = f"{MOTIVO_PROFUNDIDADE}: nenhum caminho elementar a percorre em até {self.limites.profundidade} passos"
        elif self.cortou_contexto:
            motivo = MOTIVO_CONTEXTO
        else:
            motivo = MOTIVO_ELEMENTAR
        pendentes = [(i, motivo) for i in range(len(self.transicoes)) if i not in cobertas]
        return caminhos, pendentes

    # ---- cenários de borda
    def bordas(self, existentes: list[Caminho]) -> tuple[list[Caminho], list[Pendencia]]:
        """Para cada comparação das guardas, um cenário na fronteira e outro com o primeiro valor fora dela."""
        vistos = {(c.contexto, c.passos) for c in existentes}
        novos, omitidas = [], []
        for i, t in enumerate(self.transicoes):
            arvore = self.arvores[i]
            if not isinstance(arvore, ast.AST):
                continue
            for comparacao in _comparacoes(arvore, self.variaveis):
                resultado = self._borda(i, comparacao)
                if isinstance(resultado, str):
                    omitidas.append(Pendencia(f"{t.get('id', i)}: {comparacao.texto}", resultado))
                    continue
                for caminho in resultado:
                    if (caminho.contexto, caminho.passos) not in vistos:
                        vistos.add((caminho.contexto, caminho.passos))
                        novos.append(caminho)
        return novos, omitidas

    def _valor_do_outro(self, comparacao: _Comparacao, ambiente: dict):
        try:
            valor = expressoes.avaliar(comparacao.outro, ambiente)
        except ERROS_DE_AVALIACAO:
            return None
        return valor.isoformat() if isinstance(valor, date) else valor

    def _contextos_da_borda(self, comparacao: _Comparacao, camada: int):
        """Contextos de sondagem; se a variável da comparação é de contexto, ela começa na fronteira."""
        variavel = comparacao.variavel
        if self.variaveis[variavel]["categoria"] != "contexto":
            yield from self._contextos(camada)
            return
        tipo = self.variaveis[variavel]["tipo"]
        for contexto in self._contextos(camada, fixos={variavel: None}):
            inicios = _inicios(comparacao.operador, self._valor_do_outro(comparacao, contexto), tipo)
            if inicios is not None and _na_camada(inicios[0], tipo, camada):
                yield {**contexto, variavel: inicios[0]}

    def _valores_dos_atomos(self, atomos: list, ambiente: dict) -> dict[int, bool] | None:
        try:
            return {id(a): bool(expressoes.avaliar(a, ambiente)) for a in atomos}
        except ERROS_DE_AVALIACAO:
            return None

    def _par(self, comparacao: _Comparacao, arvore, ambiente: dict, camada: int):
        """(valor dentro, valor fora, condições no valor dentro); None sem valor dentro; "sem_fora" sem valor fora."""
        variavel = self.variaveis[comparacao.variavel]
        tipo, filtrar = variavel["tipo"], variavel["categoria"] != "estado"
        inicios = _inicios(comparacao.operador, self._valor_do_outro(comparacao, ambiente), tipo)
        if inicios is None:
            return None
        inicio_dentro, sentido_dentro, inicio_fora, sentido_fora = inicios
        atomos, chave, n = _atomos(arvore), id(comparacao.no), self.limites.passos_borda
        dentro = valores_dentro = None
        for v in _sequencia(inicio_dentro, sentido_dentro, tipo, n):
            if filtrar and not _na_camada(v, tipo, camada):
                break
            valores = self._valores_dos_atomos(atomos, {**ambiente, comparacao.variavel: v})
            if valores is not None and _decisiva(arvore, comparacao.no, valores):
                dentro, valores_dentro = v, valores
                break
        if valores_dentro is None:
            return None
        for v in _sequencia(inicio_fora, sentido_fora, tipo, n):
            if filtrar and not _na_camada(v, tipo, camada):
                break
            valores = self._valores_dos_atomos(atomos, {**ambiente, comparacao.variavel: v})
            if valores is None or valores[chave] == valores_dentro[chave]:
                continue
            if all(valores[k] == valores_dentro[k] for k in valores_dentro if k != chave):
                return dentro, v, valores_dentro
        return "sem_fora"

    def _borda(self, i: int, comparacao: _Comparacao):
        """Os dois cenários da borda, ou o motivo de não gerá-los."""
        t, arvore = self.transicoes[i], self.arvores[i]
        variavel = comparacao.variavel
        # O par de valores só depende das variáveis da guarda (fora a da comparação): sondagens iguais são puladas
        relevantes = sorted(expressoes.variaveis_usadas(arvore) - {variavel})
        estagio, sondadas, motivo_caminho = 0, set(), MOTIVO_SEM_CAMINHO
        for camada in self.camadas:
            for contexto in self._contextos_da_borda(comparacao, camada):
                for config, _ in self._largura(self.inicio, contexto, camada, self.limites.profundidade - 1):
                    if config[0] != t["de"]:
                        continue
                    for dados in self._dados(t["de"], t["evento"], camada):
                        ambiente = self._ambiente(config, contexto, dados)
                        chave = (camada, tuple(ambiente.get(n) for n in relevantes))
                        if chave in sondadas:
                            continue
                        if len(sondadas) >= LIMITE_SONDAGENS:
                            return self._motivo_borda(estagio, motivo_caminho)
                        sondadas.add(chave)
                        estagio = max(estagio, 1)
                        par = self._par(comparacao, arvore, ambiente, camada)
                        if par is None:
                            continue
                        if par == "sem_fora":
                            estagio = max(estagio, 2)
                            continue
                        estagio = 3
                        valor_dentro, valor_fora, valores_dentro = par
                        dentro = self._cenario_da_borda(i, comparacao, contexto, camada, valor_dentro, valores_dentro, True)
                        if dentro is None:
                            motivo_caminho = (
                                f"o valor na fronteira ({variavel} = {formatar_valor(valor_dentro)}) "
                                "não forma um caminho viável"
                            )
                            continue
                        fora = self._cenario_da_borda(i, comparacao, contexto, camada, valor_fora, valores_dentro, False)
                        if fora is None:
                            motivo_caminho = (
                                f"o valor de fora ({variavel} = {formatar_valor(valor_fora)}) "
                                f"não forma um caminho viável a partir de {t['de']}"
                            )
                            continue
                        return [dentro, fora]
        return self._motivo_borda(estagio, motivo_caminho)

    def _motivo_borda(self, estagio: int, motivo_caminho: str) -> str:
        return (
            MOTIVO_ORIGEM, MOTIVO_SEM_DENTRO,
            f"sem valor de fora válido em até {self.limites.passos_borda} passos", motivo_caminho,
        )[estagio]

    def _cenario_da_borda(self, i, comparacao, contexto, camada, valor, valores_dentro, dentro):
        """Caminho com a variável da comparação no valor dado; dentro da fronteira, a transição `i` dispara."""
        t, arvore = self.transicoes[i], self.arvores[i]
        variavel = comparacao.variavel
        categoria = self.variaveis[variavel]["categoria"]
        if categoria == "contexto":
            contexto = {**contexto, variavel: valor}
        atomos, chave = _atomos(arvore), id(comparacao.no)
        for config, passos in self._largura(self.inicio, contexto, camada, self.limites.profundidade - 1):
            if config[0] != t["de"]:
                continue
            if categoria == "estado" and dict(zip(self.de_estado, config[1])).get(variavel) != valor:
                continue
            for dados in self._dados(t["de"], t["evento"], camada):
                if categoria == "entrada":
                    dados = {**dados, variavel: valor}
                valores = self._valores_dos_atomos(atomos, self._ambiente(config, contexto, dados))
                if valores is None:
                    continue
                if dentro and not _decisiva(arvore, comparacao.no, valores):
                    continue
                if not dentro and (
                    valores[chave] == valores_dentro[chave]
                    or any(valores[k] != valores_dentro[k] for k in valores_dentro if k != chave)
                ):
                    continue
                j, nova = self._disparar(config, contexto, t["evento"], dados)
                if j is _FALHA or (dentro and j != i):
                    continue
                passo = Passo(t["evento"], tuple(dados.items()), j, nova[0])
                if j is None:  # recusado: o cenário termina na recusa
                    return self._caminho(contexto, (*passos, passo), borda=True)
                resto = self._ate_final(nova, contexto, camada, self.limites.profundidade - len(passos) - 1)
                if resto is not None:
                    return self._caminho(contexto, (*passos, passo, *resto), borda=True)
        return None
