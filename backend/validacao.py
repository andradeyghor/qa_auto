"""Validação da saída do LLM (passo 1.4): extração do JSON, estrutura e coerência do grafo."""
import json
import re
from collections import deque

from pydantic import ValidationError

from .schemas import ModeloMBT


class ErroModelo(Exception):
    """A resposta do LLM não gerou um modelo MBT válido."""


def extrair_json(texto: str) -> dict:
    """Remove cercas de markdown / texto extra e converte para dict."""
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.IGNORECASE)
    ini, fim = texto.find("{"), texto.rfind("}")
    if ini == -1 or fim == -1 or fim < ini:
        raise ErroModelo("A resposta não contém um objeto JSON.")
    try:
        return json.loads(texto[ini : fim + 1])
    except json.JSONDecodeError as e:
        raise ErroModelo(f"JSON inválido: {e}") from e


def numeros_de_criterios(criterios: str) -> set[int]:
    """Extrai os números das linhas de critérios (ex.: '1. ...' ou '2) ...')."""
    return {int(n) for n in re.findall(r"^\s*(\d+)\s*[.)\-:]", criterios, flags=re.MULTILINE)}


def validar_coerencia(modelo: ModeloMBT, criterios: str = "") -> None:
    estados = modelo.estados
    if not estados:
        raise ErroModelo("A lista de estados está vazia.")
    if len(set(estados)) != len(estados):
        raise ErroModelo("Há estados duplicados na lista de estados.")
    conjunto = set(estados)
    if modelo.inicial not in conjunto:
        raise ErroModelo(f"O estado inicial '{modelo.inicial}' não está na lista de estados.")
    if not modelo.transicoes:
        raise ErroModelo("Não há nenhuma transição.")
    for t in modelo.transicoes:
        for extremo in (t.de, t.para):
            if extremo not in conjunto:
                raise ErroModelo(
                    f"O estado '{extremo}' aparece em uma transição mas não está na lista de estados."
                )

    # Alcançabilidade a partir do estado inicial (BFS)
    vizinhos: dict[str, set[str]] = {e: set() for e in estados}
    for t in modelo.transicoes:
        vizinhos[t.de].add(t.para)
    visitados, fila = {modelo.inicial}, deque([modelo.inicial])
    while fila:
        for prox in vizinhos[fila.popleft()]:
            if prox not in visitados:
                visitados.add(prox)
                fila.append(prox)
    inalcancaveis = conjunto - visitados
    if inalcancaveis:
        raise ErroModelo(
            f"Estados inalcançáveis a partir do inicial: {', '.join(sorted(inalcancaveis))}."
        )

    # Cobertura dos critérios de aceite
    esperados = numeros_de_criterios(criterios)
    cobertos = {t.criterio for t in modelo.transicoes if t.criterio is not None}
    faltando = esperados - cobertos
    if faltando:
        lista = ", ".join(str(n) for n in sorted(faltando))
        raise ErroModelo(f"Critérios de aceite sem nenhuma transição associada: {lista}.")


def validar_resposta(texto: str, criterios: str = "") -> ModeloMBT:
    dados = extrair_json(texto)
    try:
        modelo = ModeloMBT.model_validate(dados)
    except ValidationError as e:
        resumo = "; ".join(
            f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()
        )
        raise ErroModelo(f"Estrutura inválida: {resumo}") from e
    validar_coerencia(modelo, criterios)
    return modelo
