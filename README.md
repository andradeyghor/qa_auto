# 🤖 QA Autonomous

Ferramenta de Geração Automática de Testes de Software utilizando Processamento de Linguagem Natural (PLN) e Model-Based Testing (MBT).

## Objetivo

Transformar **User Stories** e **Critérios de Aceite** em:

- **Grafos de Estado** (Mermaid)
- **Cenários BDD** (Gherkin)
- **Scripts de teste** (Pytest / pytest-bdd)

A geração é feita com LLMs (Gemini na nuvem ou Ollama local). A versão atual é um protótipo com saída simulada (mock).

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
streamlit run app.py
```

## Estrutura

- `app.py` – interface Streamlit
- `backend/` – futura API FastAPI
- `database/` – futuro SQLite
- `tests/` – testes gerados

## Autor

Juan Cezar Yghor Andrade — Fatec Cotia
