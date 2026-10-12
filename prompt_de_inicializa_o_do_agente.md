# Contexto do Projeto: QA Autonomous
Você é um Engenheiro de Software Sênior especialista em Python, Streamlit e testes automatizados. Sua missão é inicializar um repositório Git local e criar a estrutura completa de arquivos para o projeto acadêmico "QA Autonomous" (Fatec Cotia - Aluno: Juan Cezar Yghor Andrade).

O projeto é uma Ferramenta de Geração Automática de Testes de Software utilizando Processamento de Linguagem Natural (PLN) e Model-Based Testing (MBT). A interface do usuário é construída com Streamlit.

# Suas Tarefas
Por favor, execute os seguintes passos de forma sequencial para configurar o projeto na minha máquina:

## 1. Inicialização do Repositório
- Inicialize um repositório Git vazio no diretório atual.
- Crie um arquivo `.gitignore` padrão para Python (ignorando `__pycache__`, `.venv`, `.env`, arquivos de sistema operacional, etc.).

## 2. Criação da Estrutura de Arquivos
Crie os seguintes arquivos com seus respectivos conteúdos:

### Arquivo: `requirements.txt`
```text
streamlit>=1.30.0
pytest>=7.0.0
pytest-bdd>=7.0.0
```

### Arquivo: `README.md`
Crie um README profissional detalhando:
- O nome do projeto (QA Autonomous).
- O objetivo: Transformar User Stories e Critérios de Aceite em Grafos de Estado (Mermaid), Cenários BDD (Gherkin) e Scripts (Pytest) usando LLMs.
- Instruções de instalação e execução (`pip install -r requirements.txt` e `streamlit run app.py`).
- O autor: Juan Cezar Yghor Andrade (Fatec Cotia).

### Arquivo: `app.py`
Crie o arquivo principal da aplicação utilizando exatamente o código abaixo:

```python
import streamlit as st
import streamlit.components.v1 as components
import time

# 1. Configuração da Página
st.set_page_config(
    page_title="QA Autonomous",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Função Helper para renderizar Mermaid.js no Streamlit
def render_mermaid(mermaid_code: str):
    \"\"\"Renderiza código Mermaid via injeção de HTML e Javascript\"\"\"
    html_code = f\"\"\"
    <div class="mermaid" style="display: flex; justify-content: center; margin-top: 20px;">
        {mermaid_code}
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    \"\"\"
    components.html(html_code, height=500, scrolling=True)

# 3. Cabeçalho e Barra Lateral
st.title("🤖 QA Autonomous")
st.markdown("**Ferramenta de Geração Automática de Testes com NLP e Model-Based Testing (MBT)**")

with st.sidebar:
    st.header("⚙️ Configurações")
    modelo_selecionado = st.selectbox("Motor LLM", ["Gemini (Cloud)", "Ollama (Local)"])
    st.markdown("---")
    st.info("Fatec Cotia\\n\\nProjeto: Processamento de Linguagem Natural\\n\\nAluno: Juan Cezar Yghor Andrade")

# 4. Layout Principal (Entradas e Saídas)
col_input, col_output = st.columns([1, 2], gap="large")

with col_input:
    st.subheader("1. Entradas (Requisitos)")
    
    user_story = st.text_area(
        "User Story",
        value="Como um cliente bancário,\\nQuero realizar o login no sistema,\\nPara acessar minha conta corrente.",
        height=100
    )
    
    criterios = st.text_area(
        "Critérios de Aceite",
        value="1. Senha correta redireciona para o Dashboard.\\n2. Senha incorreta exibe mensagem de erro.\\n3. Três tentativas erradas bloqueiam a conta.",
        height=150
    )
    
    gerar_btn = st.button("🚀 Gerar Modelo e Testes", type="primary", use_container_width=True)

with col_output:
    st.subheader("2. Artefatos Gerados (MBT & BDD)")
    
    if gerar_btn:
        with st.spinner(f"Processando requisitos com {modelo_selecionado}... Extraindo Estados e Transições..."):
            time.sleep(2) # Mock do processamento LLM
            
            mock_mermaid = \"\"\"
            stateDiagram-v2
                [*] --> Deslogado
                Deslogado --> ValidandoCredenciais : Submeter Login
                ValidandoCredenciais --> Dashboard : Sucesso
                ValidandoCredenciais --> Deslogado : Falha (Tentativas < 3)
                ValidandoCredenciais --> ContaBloqueada : Falha (Tentativas >= 3)
                Dashboard --> [*]
            \"\"\"
            
            mock_gherkin = \"\"\"Feature: Login do Cliente Bancário
  Como um cliente bancário
  Quero realizar o login no sistema
  Para acessar minha conta corrente

  Scenario: Login com sucesso
    Given que o usuário está no estado "Deslogado"
    When submeter as credenciais corretas
    Then o sistema transita para o estado "Dashboard"
\"\"\"
            mock_pytest = \"\"\"import pytest
from pytest_bdd import scenarios, given, when, then

scenarios('login.feature')

@given('que o usuário está no estado "Deslogado"')
def estado_inicial():
    pass

@when('submeter as credenciais corretas')
def submeter_credenciais():
    pass

@then('o sistema transita para o estado "Dashboard"')
def validar_dashboard():
    assert True
\"\"\"

            tab1, tab2, tab3 = st.tabs(["📊 Grafo de Estados (Mermaid)", "📝 Cenários BDD (Gherkin)", "💻 Script (Pytest)"])
            
            with tab1:
                st.markdown("Visualização da extração estruturada de nós e transições críticas.")
                render_mermaid(mock_mermaid)
                
            with tab2:
                st.code(mock_gherkin, language="gherkin")
                st.download_button("Baixar login.feature", data=mock_gherkin, file_name="login.feature", mime="text/plain")
                
            with tab3:
                st.code(mock_pytest, language="python")
                st.download_button("Baixar test_login.py", data=mock_pytest, file_name="test_login.py", mime="text/x-python")
    else:
        st.info("👈 Preencha os requisitos e clique em gerar para visualizar a análise MBT.")
```

## 3. Estrutura de Diretórios Adicionais
Crie as seguintes pastas vazias (com um arquivo `.gitkeep` dentro de cada) para preparar a arquitetura futura delineada no projeto:
- `backend/` (para a futura API FastAPI)
- `database/` (para o futuro SQLite)
- `tests/` (para alocar os testes gerados)

## 4. Finalização
Após criar todos os arquivos e pastas, faça o commit inicial com a mensagem "feat: Initial commit with Streamlit prototype for QA Autonomous" e me avise que o ambiente está pronto para execução.