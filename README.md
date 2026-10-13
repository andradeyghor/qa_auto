# 🤖 QA Autonomous — Interface & Front-End (PLN / MBT)

> **Projeto Semestral — Processamento de Linguagem Natural (PLN)**  
> **Instituição:** Faculdade de Tecnologia de Cotia (Fatec Cotia)  
> **Autor:** Juan Cezar Yghor Andrade  
> **Foco desta Entrega:** **Front-End & Interface do Usuário (Streamlit)**

---

> [!IMPORTANT]
> **Escopo da Entrega Atual: Front-End**  
> Esta entrega compreende a **interface visual interativa**, projetada em **Streamlit**, com foco na experiência do usuário (UX), ingestão de requisitos em linguagem natural e visualização dos modelos de teste.  
> A aplicação inclui um **Modo Demonstração autônomo** (Zero Setup), permitindo avaliar todas as telas, transições, métricas e renderização de grafos Mermaid.js sem dependência de chaves de API ou serviços externos.

---

## 📌 Visão Geral do Front-End

A interface do **QA Autonomous** foi desenvolvida para servir de ponte entre a especificação de software em linguagem natural e a modelagem formal de testes (Model-Based Testing — MBT).

### O que foi implementado nesta entrega:
1. **Entrada e Ingestão de Requisitos:**
   - Campos dedicados para inserção de **User Story** e **Critérios de Aceite**.
   - Contador em tempo real de caracteres e detecção automática da quantidade de critérios.
   - **Upload de arquivos (`.txt` e `.md`)** com rotina de separação inteligente entre história e critérios de aceite.
2. **Visualização Interativa de Model-Based Testing:**
   - **Grafo de Estados Dinâmico:** Renderização vetorial via Mermaid.js em container isolado.
   - **Tabela de Transições:** Detalhamento de estado de origem, evento disparador, estado destino e critério vinculado.
   - **Painel de Métricas:** Contagem de estados, transições, latência e percentual de cobertura dos critérios.
3. **Pré-visualização e Exportação de Artefatos:**
   - Abas estruturadas para inspeção do JSON do modelo, cenários BDD (*Gherkin*) e scripts *Pytest*.
   - Botões de download para os artefatos gerados (`.feature` e `.py`).
4. **Painel de Configurações (Barra Lateral):**
   - Seletor de motor de IA (Gemini Cloud vs. Ollama Local).
   - Inserção de API Key diretamente pela interface gráfica (evita a necessidade de configurar arquivos `.env`).
   - Carregador de casos de exemplo reais para teste rápido.

---

## 🚦 Status do Projeto & Roadmap

| Componente | Status | Descrição |
| :--- | :---: | :--- |
| **Interface com Usuário (Front-End)** | ✅ **Entregue** | Interface Streamlit completa, responsiva, com upload, métricas e grafos Mermaid. |
| **Modo Demonstração (Mock / Demo)** | ✅ **Entregue** | Casos de teste pré-carregados para avaliação imediata de UX e visualização. |
| **Integração com Backend / LLMs** | 🟡 *Em andamento* | Protótipo funcional em `backend/` com endpoints FastAPI para inferência real. |
| **Geração de Scripts BDD / Pytest** | ⏳ *Próxima etapa* | Compilação automática dos caminhos do grafo em arquivos executáveis. |

---

## 🚀 Como Executar o Front-End para Avaliação

### 1. Pré-requisitos
- **Python 3.10** ou superior instalado.

### 2. Instalação

```bash
# 1. Crie o ambiente virtual
python -m venv .venv

# 2. Ative o ambiente virtual
# No Windows:
.venv\Scripts\activate
# No Linux/macOS:
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt
```

---

### 3. Inicialização do Front-End

Para testar e avaliar a interface imediatamente:

```bash
streamlit run app.py
```

A aplicação abrirá no seu navegador em `http://localhost:8501`.

> 💡 **Dica de Avaliação:**
> O **"Modo demonstração"** já vem ativado por padrão na barra lateral. Você pode selecionar os exemplos (*Autenticação*, *Carrinho*, etc.) no seletor da esquerda e clicar em **"🚀 Gerar Modelo e Testes"** para ver a interface e o grafo Mermaid em ação instantaneamente.

---

### 4. (Opcional) Execução com Backend Real

Caso deseje testar a integração com o backend experimental em FastAPI:

**Terminal 1 — Backend:**
```bash
uvicorn backend.main:app --reload
```

**Terminal 2 — Frontend:**
```bash
streamlit run app.py
```
*(Desative o "Modo demonstração" na barra lateral e informe sua chave do Gemini, se desejado).*

---

## 🧪 Testes Unitários

Para rodar os testes de validação dos esquemas e dados da interface:

```bash
pytest tests
```

---

## 📁 Estrutura do Repositório

```text
qa_auto/
├── app.py                # ⭐ Aplicação principal do Front-End (Streamlit)
├── demo_data.py          # Dados simulados e exemplos para o Modo Demonstração
├── requirements.txt      # Dependências do projeto
├── pytest.ini            # Configuração de execução dos testes
│
├── backend/              # Protótipo do serviço de processamento e LLM (FastAPI)
│   ├── main.py
│   ├── schemas.py
│   ├── prompts.py
│   ├── llm.py
│   ├── servico.py
│   └── validacao.py
│
└── tests/                # Suíte de testes automatizados
    └── test_passo1.py
```

---

## 🛠️ Tecnologias do Front-End

- **Streamlit:** Framework de interface web reativa em Python.
- **Mermaid.js:** Biblioteca JavaScript para renderização declarativa de autômatos e grafos de transição de estados.
- **CSS3 / HTML5:** Estilização customizada em *Light Mode* com layout limpo e tipografia moderna (*Inter*).

---

## 👨‍💻 Autor

- **Juan Cezar Yghor Andrade**  
- Curso de Análise e Desenvolvimento de Sistemas — Fatec Cotia  
- Disciplina: *Processamento de Linguagem Natural (PLN)*
