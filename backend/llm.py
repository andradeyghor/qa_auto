"""Clientes LLM (passo 1.3): Gemini e Ollama com a mesma assinatura."""
import os

from dotenv import load_dotenv

from .schemas import ModeloMBT

load_dotenv()

TEMPERATURA = 0.1
TIMEOUT_SEGUNDOS = 90


class ErroLLM(Exception):
    """Falha ao se comunicar com o motor LLM (chave, rede, serviço fora do ar...)."""


def _chamar_gemini(system: str, mensagens: list[dict]) -> str:
    from google import genai
    from google.genai import types

    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        raise ErroLLM("GEMINI_API_KEY não configurada. Defina-a no arquivo .env.")
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in mensagens
    ]
    try:
        client = genai.Client(
            api_key=chave,
            http_options=types.HttpOptions(timeout=TIMEOUT_SEGUNDOS * 1000),
        )
        resp = client.models.generate_content(
            model=modelo,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=TEMPERATURA,
                response_mime_type="application/json",
                response_schema=ModeloMBT,
            ),
        )
        return resp.text or ""
    except Exception as e:  # noqa: BLE001
        raise ErroLLM(f"Erro ao chamar o Gemini: {e}") from e


def _chamar_ollama(system: str, mensagens: list[dict]) -> str:
    import ollama

    modelo = os.getenv("OLLAMA_MODEL", "llama3.1")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        client = ollama.Client(host=host, timeout=TIMEOUT_SEGUNDOS)
        resp = client.chat(
            model=modelo,
            messages=[{"role": "system", "content": system}, *mensagens],
            format=ModeloMBT.model_json_schema(),
            options={"temperature": TEMPERATURA},
        )
        return resp["message"]["content"]
    except Exception as e:  # noqa: BLE001
        raise ErroLLM(
            f"Erro ao chamar o Ollama (o servidor está rodando e o modelo '{modelo}' foi baixado?): {e}"
        ) from e


def chamar_llm(motor: str, system: str, mensagens: list[dict]) -> str:
    if motor == "Gemini (Cloud)":
        return _chamar_gemini(system, mensagens)
    if motor == "Ollama (Local)":
        return _chamar_ollama(system, mensagens)
    raise ErroLLM(f"Motor desconhecido: {motor}")
