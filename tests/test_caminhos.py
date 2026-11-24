"""Caminhos de teste viáveis, estratégias, bordas e cobertura (add-mbt-generator, tarefas 1.1 a 1.6)."""
import copy

import pytest

import exemplos
from backend.caminhos import (
    ELEMENTARES,
    MOTIVO_PROFUNDIDADE,
    TRANSICOES,
    Limites,
    gerar_caminhos,
)
from backend.cobertura import calcular
from backend.geracao import gerar_artefatos
from backend.schemas import ModeloEstados, estados_finais
from backend.simulador import SimuladorModelo
from backend.validacao import validar_modelo
from sistemas_exemplo import obter

GABARITOS = ("saque-atm", "cupom-promocional", "mfa-bloqueio", "carrinho")


def gabarito(gabarito_id):
    return exemplos.carregar(gabarito_id)["modelo"]


def modelos_de_referencia():
    return [(g, gabarito(g)) for g in GABARITOS] + [(s, obter(s).modelo) for s in ("login", "saque")]


def com_saldo(valor):
    modelo = copy.deepcopy(gabarito("saque-atm"))
    next(v for v in modelo["variaveis"] if v["nome"] == "saldo")["valor_inicial"] = valor
    return modelo


def ids(modelo, caminho):
    return [modelo["transicoes"][i]["id"] if i is not None else None for i in (p.transicao for p in caminho.passos)]


def caminho_ate(modelo, resultado, estado):
    return next(c for c in resultado.caminhos if c.final == estado and not c.borda)


def reproduzir(modelo, caminho):
    """Executa o caminho no simulador e confere aceitação e estado de cada passo."""
    simulador = SimuladorModelo(modelo)
    for nome, valor in caminho.contexto:
        simulador.definir_contexto(nome, valor)
    for passo in caminho.passos:
        assert simulador.disparar(passo.evento, dict(passo.dados)) == passo.aceito, passo
        assert simulador.estado_atual == passo.estado, passo


def modelo(estados, transicoes, variaveis=()):
    return {
        "analise": "",
        "variaveis": list(variaveis),
        "estados": [{"id": e, "rotulo": e, "tipo": t} for e, t in estados],
        "transicoes": [
            {"id": f"T{n}", "de": de, "evento": ev, "para": para, "guarda": g, "acoes": list(a), "criterios": list(c)}
            for n, (de, ev, para, g, a, c) in enumerate(transicoes, start=1)
        ],
    }


VALOR = {"nome": "valor", "tipo": "decimal", "categoria": "entrada", "valor_inicial": None}
CONTADOR = {"nome": "contador", "tipo": "inteiro", "categoria": "estado", "valor_inicial": 0}

GUARDA_ZERO = modelo(
    [("Inicio", "inicial"), ("Aceito", "final"), ("Recusado", "final")],
    [("Inicio", "enviar", "Aceito", "valor > 0", [], [1]), ("Inicio", "enviar", "Recusado", "valor <= 0", [], [2])],
    [VALOR],
)

PROFUNDO = modelo(
    [("Inicio", "inicial"), ("Fim", "final")],
    [
        ("Inicio", "incrementar", "Inicio", "contador < 40", ["contador += 1"], [1]),
        ("Inicio", "encerrar", "Fim", "contador >= 35", [], [2]),
        ("Inicio", "desistir", "Fim", None, [], [3]),
    ],
    [CONTADOR],
)

# Oito escolhas seguidas entre dois eventos: 2**8 = 256 caminhos elementares
BINARIO = modelo(
    [("S0", "inicial"), *((f"S{i}", "intermediario") for i in range(1, 8)), ("S8", "final")],
    [t for i in range(8) for t in ((f"S{i}", "a", f"S{i + 1}", None, [], []), (f"S{i}", "b", f"S{i + 1}", None, [], []))],
)

# Fora da fronteira de "valor <= 10", a outra condição ("não valor > 10") sempre muda junto
SEM_FORA = modelo(
    [("Inicio", "inicial"), ("Fim", "final"), ("Acima", "final")],
    [("Inicio", "enviar", "Fim", "valor <= 10 e não valor > 10", [], [1]), ("Inicio", "enviar", "Acima", "valor > 10", [], [2])],
    [VALOR],
)

# Acima de 10 nenhuma transição aceita o evento
RECUSA = modelo([("Inicio", "inicial"), ("Fim", "final")], [("Inicio", "enviar", "Fim", "valor <= 10", [], [1])], [VALOR])


@pytest.mark.parametrize("m", [GUARDA_ZERO, PROFUNDO, BINARIO, SEM_FORA, RECUSA], ids=["zero", "profundo", "binario",
                                                                                      "sem_fora", "recusa"])
def test_modelos_de_teste_sao_validos(m):
    assert validar_modelo(ModeloEstados.model_validate(m)) == []


# ---------------------------------------------------------------- 1.1 candidatos e busca por configurações
def test_contador_percorrido_ate_reter_o_cartao():
    m = gabarito("saque-atm")
    retido = caminho_ate(m, gerar_caminhos(m), "CartaoRetido")
    assert [p.evento for p in retido.passos].count("pin_invalido") == 3


def test_caminho_normal_usa_valores_positivos():
    m = gabarito("saque-atm")
    realizado = caminho_ate(m, gerar_caminhos(m, bordas=False), "SaqueRealizado")
    assert dict(realizado.contexto) == {"saldo": 20}
    assert dict(realizado.passos[-1].dados) == {"valor": 20}


def test_valor_de_contexto_declarado_vem_primeiro():
    m = com_saldo(100)
    realizado = caminho_ate(m, gerar_caminhos(m, bordas=False), "SaqueRealizado")
    assert dict(realizado.contexto) == {"saldo": 100}
    assert dict(realizado.passos[-1].dados) == {"valor": 20}


def test_zero_quando_a_guarda_pede():
    recusado = caminho_ate(GUARDA_ZERO, gerar_caminhos(GUARDA_ZERO, bordas=False), "Recusado")
    assert dict(recusado.passos[-1].dados) == {"valor": 0}
    aceito = caminho_ate(GUARDA_ZERO, gerar_caminhos(GUARDA_ZERO, bordas=False), "Aceito")
    assert dict(aceito.passos[-1].dados)["valor"] > 0


def test_caminho_informa_transicoes_valores_e_criterios():
    m = gabarito("saque-atm")
    realizado = caminho_ate(m, gerar_caminhos(m, bordas=False), "SaqueRealizado")
    assert ids(m, realizado) == ["T1", "T2", "T5"]
    assert realizado.criterios(m) == [1, 2, 4]
    assert dict(realizado.contexto) and realizado.passos[-1].dados


# ---------------------------------------------------------------- 1.2 todas as transições, até um estado final
@pytest.mark.parametrize("nome, m", modelos_de_referencia(), ids=[n for n, _ in modelos_de_referencia()])
def test_todas_as_transicoes_cobertas_por_caminhos_viaveis(nome, m):
    resultado = gerar_caminhos(m, TRANSICOES, bordas=False)
    assert not resultado.transicoes_pendentes
    assert {i for c in resultado.caminhos for i in c.indices()} == set(range(len(m["transicoes"])))
    assert calcular(m, resultado).percentual(calcular(m, resultado).transicoes) == 100
    for caminho in resultado.caminhos:
        assert caminho.final in estados_finais(m)
        reproduzir(m, caminho)


def test_caminhos_mais_curtos_e_cada_um_acrescenta_cobertura():
    m = obter("login").modelo
    caminhos = gerar_caminhos(m, bordas=False).caminhos
    assert [ids(m, c) for c in caminhos] == [["T1"], ["T2", "T3"], ["T2", "T4", "T5"], ["T2", "T4", "T6"]]


# ---------------------------------------------------------------- 1.3 caminhos elementares
def test_elementares_nao_repetem_configuracao_e_terminam_num_final():
    m = gabarito("saque-atm")
    resultado = gerar_caminhos(m, ELEMENTARES, bordas=False)
    assert len(resultado.caminhos) == 7
    for caminho in resultado.caminhos:
        reproduzir(m, caminho)
        assert caminho.final in estados_finais(m)
    assert ["T1", "T3", "T3", "T2", "T5"] in [ids(m, c) for c in resultado.caminhos]


def test_elementares_avisam_o_limite_atingido():
    resultado = gerar_caminhos(BINARIO, ELEMENTARES, bordas=False)
    assert len(resultado.caminhos) == 200
    assert any("Limite de 200 caminhos atingido" in a for a in resultado.avisos)
    assert "Limite de 200 caminhos" in calcular(BINARIO, resultado).em_markdown()


def test_elementares_sem_limite_listam_todos():
    resultado = gerar_caminhos(BINARIO, ELEMENTARES, bordas=False, limites=Limites(caminhos=300))
    assert len(resultado.caminhos) == 256 and not resultado.avisos


def test_estrategia_desconhecida():
    with pytest.raises(ValueError, match="largura"):
        gerar_caminhos(BINARIO, "largura")


# ---------------------------------------------------------------- 1.4 cenários de borda
def test_borda_do_saldo_declarado():
    m = com_saldo(100)
    bordas = [c for c in gerar_caminhos(m).caminhos if c.borda]
    valores = sorted(dict(c.passos[-1].dados)["valor"] for c in bordas if c.passos[-1].dados)
    assert valores == [100, 120]
    assert {c.final for c in bordas} == {"SaqueRealizado", "SaqueRecusado"}
    for caminho in bordas:
        reproduzir(m, caminho)


def test_borda_sem_valor_de_fora_valido_vai_para_o_relatorio():
    resultado = gerar_caminhos(SEM_FORA)
    omitidas = {p.item: p.motivo for p in resultado.bordas_omitidas}
    assert omitidas["T1: valor <= 10"] == "sem valor de fora válido em até 10000 passos"
    assert "T1: valor <= 10" in calcular(SEM_FORA, resultado).em_markdown()


def test_evento_recusado_na_borda():
    resultado = gerar_caminhos(RECUSA)
    recusado = next(c for c in resultado.caminhos if c.borda and not c.passos[-1].aceito)
    assert dict(recusado.passos[-1].dados) == {"valor": 10.01}
    assert recusado.final == "Inicio"
    reproduzir(RECUSA, recusado)


def test_sem_bordas():
    assert not [c for c in gerar_caminhos(com_saldo(100), bordas=False).caminhos if c.borda]


def test_bordas_de_contador_e_de_contexto():
    mfa = gabarito("mfa-bloqueio")
    borda = next(c for c in gerar_caminhos(mfa).caminhos if c.borda)
    assert ids(mfa, borda) == ["T1", "T4", "T4", "T3"]  # dois códigos errados ainda não bloqueiam
    cupom = gabarito("cupom-promocional")
    for caminho in gerar_caminhos(cupom).caminhos:
        reproduzir(cupom, caminho)


# ---------------------------------------------------------------- 1.5 relatório de cobertura
def test_transicao_alem_da_profundidade_maxima():
    resultado = gerar_caminhos(PROFUNDO, bordas=False)
    cobertura = calcular(PROFUNDO, resultado)
    assert dict(resultado.transicoes_pendentes) == {1: MOTIVO_PROFUNDIDADE}
    assert ("Transição", "T2", MOTIVO_PROFUNDIDADE) in [(i.tipo, i.nome, i.motivo) for i in cobertura.nao_cobertos]
    assert any(i.tipo == "Critério" and i.nome == "CA2" for i in cobertura.nao_cobertos)
    assert cobertura.transicoes == (2, 3) and cobertura.percentual(cobertura.transicoes) == 67


def test_cobertura_total():
    m = gabarito("saque-atm")
    cobertura = gerar_artefatos(m).cobertura
    assert (cobertura.percentual(cobertura.estados), cobertura.percentual(cobertura.transicoes),
            cobertura.percentual(cobertura.criterios)) == (100, 100, 100)
    assert "transições 6/6 (100%)" in cobertura.resumo()
    assert not cobertura.nao_cobertos


# ---------------------------------------------------------------- 1.6 determinismo
@pytest.mark.parametrize("estrategia", [TRANSICOES, ELEMENTARES])
@pytest.mark.parametrize("nome, m", modelos_de_referencia(), ids=[n for n, _ in modelos_de_referencia()])
def test_duas_execucoes_byte_a_byte(nome, m, estrategia):
    primeira = gerar_artefatos(m, estrategia=estrategia)
    segunda = gerar_artefatos(copy.deepcopy(m), estrategia=estrategia)
    assert primeira == segunda
    assert primeira.arquivos() == segunda.arquivos()
    assert primeira.zip() == segunda.zip()
