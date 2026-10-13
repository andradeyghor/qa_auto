"""Esquemas Pydantic: entrada (passo 1.2) e modelo MBT (passo 1.4)."""
from typing import Literal

from pydantic import BaseModel, field_validator

MAX_CARACTERES = 2000
MOTORES = ("Gemini (Cloud)", "Ollama (Local)")


class Requisicao(BaseModel):
    user_story: str
    criterios: str
    motor: Literal["Gemini (Cloud)", "Ollama (Local)"]
    api_key: str | None = None

    @field_validator("user_story", "criterios")
    @classmethod
    def limpar_e_validar(cls, valor: str, info) -> str:
        # Normaliza quebras de linha e remove espaços nas pontas
        valor = valor.replace("\r\n", "\n").replace("\r", "\n").strip()
        nome = "A User Story" if info.field_name == "user_story" else "Os Critérios de Aceite"
        if not valor:
            raise ValueError(f"{nome} não pode estar vazio(a).")
        if len(valor) > MAX_CARACTERES:
            raise ValueError(f"{nome} excede {MAX_CARACTERES} caracteres.")
        return valor


class Transicao(BaseModel):
    de: str
    evento: str
    para: str
    criterio: int | None = None


class ModeloMBT(BaseModel):
    estados: list[str]
    inicial: str
    transicoes: list[Transicao]
