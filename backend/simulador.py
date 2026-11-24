"""Semântica de execução do modelo de estados, usada pelo gerador de caminhos e pelo adaptador de simulação.

Um evento é aceito pela primeira transição declarada que parte do estado atual com esse evento e cuja guarda é
verdadeira. Sem nenhuma, o evento é recusado e nada muda. As ações alteram variáveis; só as de estado e de
contexto persistem, e os dados de entrada valem apenas para o evento em que chegaram. É a mesma regra da
simulação da avaliação (`avaliacao/simulacao.py`).
"""
from functools import lru_cache

from . import expressoes
from .schemas import estado_inicial


@lru_cache(maxsize=2048)
def arvore_da_guarda(texto: str):
    """Árvore validada da guarda, analisada uma única vez por texto (o interpretador não altera a árvore)."""
    return expressoes.analisar_guarda(texto)


def guarda_verdadeira(transicao: dict, ambiente: dict) -> bool:
    guarda = transicao.get("guarda")
    return not guarda or bool(expressoes.avaliar(arvore_da_guarda(guarda), ambiente))


def transicao_aceita(modelo: dict, estado: str, evento: str, ambiente: dict) -> int | None:
    """Índice da transição que aceita o evento no estado, ou None se o evento é recusado."""
    for i, t in enumerate(modelo["transicoes"]):
        if t["de"] == estado and t["evento"] == evento and guarda_verdadeira(t, ambiente):
            return i
    return None


class SimuladorModelo:
    """Executa o próprio modelo com o interpretador, com o mesmo contrato do adaptador do sistema sob teste."""

    def __init__(self, modelo: dict):
        self.modelo = modelo
        self.variaveis = {v["nome"]: v for v in modelo.get("variaveis", [])}
        self.valores = {n: v["valor_inicial"] for n, v in self.variaveis.items() if v["categoria"] == "estado"}
        self.estado_atual = estado_inicial(modelo)

    def definir_contexto(self, nome: str, valor) -> None:
        variavel = self.variaveis.get(nome)
        if variavel is None or variavel["categoria"] != "contexto":
            raise KeyError(f"Variável de contexto fora do modelo: {nome}")
        self.valores[nome] = valor

    def disparar(self, evento: str, dados: dict | None = None) -> bool:
        ambiente = {**self.valores, **(dados or {})}
        indice = transicao_aceita(self.modelo, self.estado_atual, evento, ambiente)
        if indice is None:
            return False
        transicao = self.modelo["transicoes"][indice]
        novos = expressoes.executar_acoes(transicao.get("acoes") or [], ambiente)
        self.valores = {nome: novos[nome] for nome in self.valores}
        self.estado_atual = transicao["para"]
        return True
