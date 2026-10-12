import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.main import app
from backend.schemas import Requisicao
from backend.servico import MAX_TENTATIVAS, gerar_modelo
from backend.validacao import ErroModelo, validar_resposta

CRITERIOS = "1. Senha correta vai ao Dashboard.\n2. Senha incorreta mostra erro.\n3. Três erros bloqueiam."

VALIDO = {
    "estados": ["Deslogado", "Validando", "Dashboard", "Bloqueada"],
    "inicial": "Deslogado",
    "transicoes": [
        {"de": "Deslogado", "evento": "Submeter", "para": "Validando", "criterio": None},
        {"de": "Validando", "evento": "Sucesso", "para": "Dashboard", "criterio": 1},
        {"de": "Validando", "evento": "Falha", "para": "Deslogado", "criterio": 2},
        {"de": "Validando", "evento": "3a falha", "para": "Bloqueada", "criterio": 3},
    ],
}


def req(**kw):
    base = dict(user_story="Como cliente...", criterios=CRITERIOS, motor="Gemini (Cloud)")
    return Requisicao(**{**base, **kw})


# 1.2 entrada
def test_entrada_vazia():
    with pytest.raises(ValidationError):
        req(user_story="   ")


def test_entrada_longa():
    with pytest.raises(ValidationError):
        req(criterios="x" * 2001)


def test_motor_invalido():
    with pytest.raises(ValidationError):
        req(motor="Outro")


def test_entrada_limpa():
    assert req(user_story="  oi\r\n ").user_story == "oi"


# 1.4 saída
def test_json_com_cerca_markdown():
    m = validar_resposta("Aqui:\n```json\n" + json.dumps(VALIDO) + "\n```", CRITERIOS)
    assert m.inicial == "Deslogado"


def test_json_invalido():
    with pytest.raises(ErroModelo):
        validar_resposta("{nao e json}")


def test_estado_fora_da_lista():
    d = json.loads(json.dumps(VALIDO))
    d["transicoes"][0]["para"] = "Fantasma"
    with pytest.raises(ErroModelo, match="Fantasma"):
        validar_resposta(json.dumps(d))


def test_estado_inalcancavel():
    d = json.loads(json.dumps(VALIDO))
    d["estados"].append("Orfao")
    with pytest.raises(ErroModelo, match="Orfao"):
        validar_resposta(json.dumps(d))


def test_criterio_sem_transicao():
    d = json.loads(json.dumps(VALIDO))
    d["transicoes"][3]["criterio"] = None
    with pytest.raises(ErroModelo, match="3"):
        validar_resposta(json.dumps(d), CRITERIOS)


# 1.3/1.4 retry
def test_retry_corrige_na_segunda():
    ruim = json.dumps({**VALIDO, "inicial": "Nada"})
    respostas = iter([ruim, json.dumps(VALIDO)])
    chamadas = []

    def fake(motor, system, msgs):
        chamadas.append(list(msgs))
        return next(respostas)

    assert gerar_modelo(req(), chamar=fake).inicial == "Deslogado"
    assert len(chamadas) == 2
    assert "Nada" in chamadas[1][-1]["content"]  # feedback do erro enviado ao LLM


def test_retry_esgota():
    with pytest.raises(ErroModelo, match=str(MAX_TENTATIVAS)):
        gerar_modelo(req(), chamar=lambda *a: "lixo")


# API
def test_api_entrada_invalida():
    c = TestClient(app)
    r = c.post("/gerar", json={"user_story": "", "criterios": "1. a", "motor": "Gemini (Cloud)"})
    assert r.status_code == 422
