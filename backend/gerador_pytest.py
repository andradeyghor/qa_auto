"""Arquivos executáveis do pacote: teste pytest-bdd, adaptador do sistema sob teste, conftest e LEIAME.

O teste tem só as seis definições genéricas do vocabulário fixo e nenhum texto do modelo. O adaptador liga os
passos ao sistema: um sistema exemplo, um esqueleto a implementar ou a simulação do próprio modelo.
"""
from . import compilador_gherkin as gherkin

MENSAGEM_ESQUELETO = "Implemente o adaptador do sistema sob teste"
SISTEMA, ESQUELETO, SIMULACAO = "sistema", "esqueleto", "simulacao"

SCRIPT = '''"""Testes gerados pelo QUALITY ASSURANCE CONSULTANT a partir de __FEATURE__.

Salve os arquivos do pacote numa pasta dentro do projeto e rode, a partir da raiz:
    python -m pytest <pasta>
__USO__
"""
import re

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("__FEATURE__")

INTEIRO = re.compile(r"-?\\d+")
DECIMAL = re.compile(r"-?\\d+\\.\\d+")


def converter(texto):
    """Valor escrito no .feature: verdadeiro/falso, inteiro, decimal ou texto (datas ficam em AAAA-MM-DD)."""
    texto = texto.strip()
    if texto in ("verdadeiro", "falso"):
        return texto == "verdadeiro"
    if INTEIRO.fullmatch(texto):
        return int(texto)
    if DECIMAL.fullmatch(texto):
        return float(texto)
    return texto


def conferir_estado(sistema, esperado):
    obtido = sistema.estado_atual
    assert obtido == esperado, f"Esperado {esperado}, obtido {obtido}"


@given(parsers.parse(__ESTADO_INICIAL__))
def passo_estado_inicial(sistema, estado):
    conferir_estado(sistema, estado)


@given(parsers.parse(__CONTEXTO__))
def passo_contexto(sistema, variavel, valor):
    sistema.definir_contexto(variavel, converter(valor))


@when(parsers.parse(__EVENTO__), target_fixture="evento_aceito")
def passo_evento(sistema, evento):
    return sistema.disparar(evento, {})


@when(parsers.parse(__EVENTO_COM_DADOS__), target_fixture="evento_aceito")
def passo_evento_com_dados(sistema, evento, datatable):
    dados = {nome.strip(): converter(valor) for nome, valor in datatable}
    return sistema.disparar(evento, dados)


@then(parsers.parse(__ESTADO__))
def passo_estado(sistema, estado):
    conferir_estado(sistema, estado)


@then(parsers.parse(__RECUSA__))
def passo_recusa(sistema, estado, evento_aceito):
    assert evento_aceito is False, "O evento deveria ter sido recusado, mas foi aceito"
    conferir_estado(sistema, estado)
'''

ADAPTADOR_SISTEMA = '''"""Adaptador do sistema sob teste: liga os passos do .feature ao sistema exemplo "__SISTEMA__".

A variante (correto ou bug) vem da variável de ambiente QA_VARIANTE.
"""
import os

from sistemas_exemplo import criar


class Adaptador:
    def __init__(self):
        self.sistema = criar("__SISTEMA__", os.getenv("QA_VARIANTE", "correto"))

    def definir_contexto(self, nome, valor):
        self.sistema.definir_contexto(nome, valor)

    def disparar(self, evento, dados):
        return self.sistema.disparar(evento, dados)

    @property
    def estado_atual(self):
        return self.sistema.estado_atual
'''

ADAPTADOR_ESQUELETO = '''"""Adaptador do sistema sob teste: implemente as três operações para ligar os testes ao seu sistema.

- definir_contexto(nome, valor): fixa um valor de contexto do cenário (ex.: saldo).
- disparar(evento, dados): envia o evento com os dados de entrada e devolve True se o sistema o aceitou.
- estado_atual: id do estado em que o sistema está, com os nomes do modelo.

Os valores chegam como bool, int, float ou texto (datas em AAAA-MM-DD).
"""
MENSAGEM = "__MENSAGEM__"


class Adaptador:
    def definir_contexto(self, nome, valor):
        raise NotImplementedError(MENSAGEM)

    def disparar(self, evento, dados):
        raise NotImplementedError(MENSAGEM)

    @property
    def estado_atual(self):
        raise NotImplementedError(MENSAGEM)
'''

ADAPTADOR_SIMULACAO = '''"""Adaptador de simulação: executa o próprio modelo (__MODELO__) com o interpretador do QUALITY ASSURANCE CONSULTANT.

Serve para testar o gerador: todo cenário gerado deve passar contra ele. Não é um sistema alvo.
"""
import json
from pathlib import Path

from backend.simulador import SimuladorModelo


class Adaptador(SimuladorModelo):
    def __init__(self):
        super().__init__(json.loads((Path(__file__).parent / "__MODELO__").read_text(encoding="utf-8")))
'''

CONFTEST = '''"""Fixture `sistema` (um adaptador novo por cenário) e registro das tags do .feature como marcas do pytest."""
import re
from pathlib import Path

import pytest

from __MODULO_ADAPTADOR__ import Adaptador


def pytest_configure(config):
    for feature in Path(__file__).parent.glob("*.feature"):
        for tag in sorted(set(re.findall(r"@([^\\s@]+)", feature.read_text(encoding="utf-8")))):
            config.addinivalue_line("markers", f"{tag}: tag do .feature")


@pytest.fixture
def sistema():
    return Adaptador()
'''

LEIAME = """# Testes gerados: __TITULO__

Pacote gerado pelo QUALITY ASSURANCE CONSULTANT a partir do modelo de estados, sem uso do LLM.

| Arquivo | Conteúdo |
|---|---|
| `__FEATURE__` | Cenários em Gherkin (`# language: pt`), um por caminho de teste |
| `__SCRIPT__` | As seis definições de passo (pytest-bdd), sem texto do modelo |
| `__ADAPTADOR__` | Liga os passos ao sistema sob teste |
| `conftest.py` | Fixture `sistema` e registro das tags do `.feature` |
| `__MODELO__` e `__DIAGRAMA__` | Modelo de estados em JSON e diagrama Mermaid |
| `cobertura.md` | Estados, transições e critérios cobertos pelos caminhos |

## Como rodar

Copie a pasta para dentro do projeto e rode, a partir da raiz:

```bash
python -m pytest <pasta>
```

Cada cenário tem as tags `@CA-<n>` dos critérios de aceite percorridos e `@caminho-<n>`; os cenários de borda
têm `@borda` e os caminhos sem critério, `@auxiliar`. Para rodar só as bordas: `python -m pytest <pasta> -m borda`.

## Adaptador

__INSTRUCOES__
"""

INSTRUCOES = {
    SISTEMA: (
        "O adaptador usa o sistema exemplo `__SISTEMA__`. Para rodar contra a variante com bug, defina "
        "`QA_VARIANTE=bug` antes do comando."
    ),
    ESQUELETO: (
        "O adaptador é um esqueleto: até ser implementado, cada cenário falha com "
        "\"__MENSAGEM__\". Implemente as três operações:\n\n"
        "- `definir_contexto(nome, valor)`: fixa um valor de contexto do cenário (ex.: saldo).\n"
        "- `disparar(evento, dados)`: envia o evento com os dados de entrada e devolve `True` se o sistema o "
        "aceitou, ou `False` se o recusou.\n"
        "- `estado_atual`: id do estado em que o sistema está, com os nomes do modelo.\n\n"
        "Os valores chegam como `bool`, `int`, `float` ou texto (datas em AAAA-MM-DD)."
    ),
    SIMULACAO: "O adaptador simula o próprio modelo com o interpretador do QUALITY ASSURANCE CONSULTANT; serve para testar o gerador.",
}

USO = {
    SISTEMA: "Para rodar contra a variante com bug, defina QA_VARIANTE=bug.",
    ESQUELETO: "O adaptador é um esqueleto: os testes falham até ele ser implementado.",
    SIMULACAO: "O adaptador simula o próprio modelo (teste do gerador).",
}


def gerar_script(nome_feature: str, modo: str) -> str:
    frases = dict(zip(
        ("__ESTADO_INICIAL__", "__CONTEXTO__", "__EVENTO__", "__EVENTO_COM_DADOS__", "__ESTADO__", "__RECUSA__"),
        gherkin.FRASES,
    ))
    texto = SCRIPT.replace("__FEATURE__", nome_feature).replace("__USO__", USO[modo])
    for marcador, frase in frases.items():
        texto = texto.replace(marcador, repr(frase))
    return texto


def gerar_adaptador(modo: str, sistema_id: str | None = None, nome_modelo: str = "") -> str:
    if modo == SISTEMA:
        return ADAPTADOR_SISTEMA.replace("__SISTEMA__", sistema_id)
    if modo == SIMULACAO:
        return ADAPTADOR_SIMULACAO.replace("__MODELO__", nome_modelo)
    return ADAPTADOR_ESQUELETO.replace("__MENSAGEM__", MENSAGEM_ESQUELETO)


def gerar_conftest(modulo_adaptador: str) -> str:
    return CONFTEST.replace("__MODULO_ADAPTADOR__", modulo_adaptador)


def gerar_leiame(titulo: str, nomes: dict[str, str], modo: str, sistema_id: str | None = None) -> str:
    instrucoes = INSTRUCOES[modo].replace("__SISTEMA__", sistema_id or "").replace("__MENSAGEM__", MENSAGEM_ESQUELETO)
    texto = LEIAME.replace("__TITULO__", gherkin.limpar(titulo)).replace("__INSTRUCOES__", instrucoes)
    for marcador, nome in nomes.items():
        texto = texto.replace(marcador, nome)
    return texto
