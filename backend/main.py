"""API FastAPI. Execute com: uvicorn backend.main:app --reload"""
from fastapi import FastAPI, HTTPException

from .llm import ErroLLM
from .schemas import ModeloMBT, Requisicao
from .servico import gerar_modelo
from .validacao import ErroModelo

app = FastAPI(title="QA Autonomous API")


@app.post("/gerar", response_model=ModeloMBT)
def gerar(req: Requisicao) -> ModeloMBT:
    try:
        return gerar_modelo(req)
    except ErroLLM as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ErroModelo as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/saude")
def saude() -> dict:
    return {"status": "ok"}
