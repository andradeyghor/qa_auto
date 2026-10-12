# 🤖 QA Autonomous

Ferramenta de Geração Automática de Testes de Software utilizando Processamento de Linguagem Natural (PLN) e Model-Based Testing (MBT).

## Objetivo

Transformar **User Stories** e **Critérios de Aceite** em:

- **Grafos de Estado** (Mermaid)
- **Cenários BDD** (Gherkin)
- **Scripts de teste** (Pytest / pytest-bdd)

A geração é feita com LLMs (Gemini na nuvem ou Ollama local). Estado atual: o front envia os requisitos ao backend, que valida a entrada, consulta o LLM e devolve um modelo de estados (JSON) validado. Gherkin e Pytest ainda serão gerados a partir desse modelo.

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # preencha GEMINI_API_KEY (ou use Ollama)
```

## Execução

Em dois terminais:

```bash
uvicorn backend.main:app --reload
streamlit run app.py
```

## Testes

```bash
pytest tests
```

## Estrutura

- `app.py` – interface Streamlit
- `backend/` – futura API FastAPI
- `database/` – futuro SQLite
- `tests/` – testes gerados

## Autor

Juan Cezar Yghor Andrade — Fatec Cotia
