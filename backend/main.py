"""API FastAPI. Execute com: uvicorn backend.main:app --reload"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import llm, servico
from .llm import ErroLLM
from .schemas import ModeloEstados, Requisicao
from .servico import ErroOrcamento
from .validacao import ErroModelo

log = logging.getLogger(__name__)

ENTRADA_INVALIDA = "entrada_invalida"
MODELO_INVALIDO = "modelo_invalido"
FALHA_PROVEDOR = "falha_provedor"
ORCAMENTO_ESGOTADO = "orcamento_esgotado"
ERRO_INTERNO = "erro_interno"


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    if os.getenv("QA_AQUECER_OLLAMA", "1") != "0":
        llm.iniciar_aquecimento()
    yield


app = FastAPI(title="QUALITY ASSURANCE CONSULTANT API", lifespan=ciclo_de_vida)


class TentativaResposta(BaseModel):
    resultado: str
    duracao: float
    erro: str = ""


class RespostaGeracao(BaseModel):
    modelo: ModeloEstados
    tentativas: int
    duracao: float
    historico: list[TentativaResposta]
    versao_prompt: str
    provedor: str
    modelo_llm: str
    deterministico: bool


def erro(status: int, codigo: str, mensagem: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={"codigo": codigo, "mensagem": mensagem, **extra})


def _mensagem_validacao(exc: RequestValidationError) -> str:
    partes = []
    for e in exc.errors():
        msg = str(e.get("msg", "")).replace("Value error, ", "")
        campo = ".".join(str(p) for p in e.get("loc", ()) if p != "body")
        partes.append(msg if e.get("type") == "value_error" or not campo else f"{campo}: {msg}")
    return "; ".join(partes) or "Requisição inválida."


@app.exception_handler(RequestValidationError)
async def _entrada_invalida(_req: Request, exc: RequestValidationError):
    return erro(422, ENTRADA_INVALIDA, _mensagem_validacao(exc))


@app.exception_handler(ErroModelo)
async def _modelo_invalido(_req: Request, exc: ErroModelo):
    return erro(422, MODELO_INVALIDO, str(exc), erros=[e.como_dict() for e in exc.erros])


@app.exception_handler(ErroLLM)
async def _falha_provedor(_req: Request, exc: ErroLLM):
    return erro(502, FALHA_PROVEDOR, str(exc))


@app.exception_handler(ErroOrcamento)
async def _orcamento(_req: Request, exc: ErroOrcamento):
    return erro(504, ORCAMENTO_ESGOTADO, str(exc))


@app.exception_handler(Exception)
async def _erro_interno(_req: Request, exc: Exception):
    log.exception("Erro interno no backend")
    return erro(500, ERRO_INTERNO, f"Erro interno no servidor: {type(exc).__name__}.")


@app.post("/gerar", response_model=RespostaGeracao)
def gerar(req: Requisicao) -> RespostaGeracao:
    resultado = servico.gerar(req)
    return RespostaGeracao(
        modelo=resultado.modelo,
        tentativas=len(resultado.tentativas),
        duracao=round(resultado.duracao, 3),
        historico=[TentativaResposta(**vars(t)) for t in resultado.tentativas],
        versao_prompt=resultado.versao_prompt,
        provedor=resultado.provedor,
        modelo_llm=resultado.modelo_llm,
        deterministico=resultado.deterministico,
    )


@app.get("/saude")
def saude() -> dict:
    provedores = llm.saude_provedores()
    return {
        "status": "ok",
        "provedores": provedores,
        # Atalhos mantidos por compatibilidade com clientes da versão anterior
        "ollama": provedores["ollama"],
        "gemini": provedores["gemini"],
        "orcamento_segundos": servico.orcamento_segundos(),
        "timeout_chamada_segundos": llm.timeout_segundos(),
    }
