import os

import requests
import streamlit as st
import streamlit.components.v1 as components

API_URL = os.getenv("QA_API_URL", "http://localhost:8000")


def modelo_para_mermaid(modelo: dict) -> str:
    """Converte o modelo MBT em stateDiagram-v2 (visualização provisória)."""
    linhas = ["stateDiagram-v2", f"    [*] --> {modelo['inicial']}"]
    for t in modelo["transicoes"]:
        evento = t["evento"].replace(":", " ")
        linhas.append(f"    {t['de']} --> {t['para']} : {evento}")
    return "\n".join(linhas)


def chamar_backend(user_story: str, criterios: str, motor: str) -> dict:
    """Envia os requisitos ao backend. Lança RuntimeError com mensagem amigável em caso de erro."""
    try:
        resp = requests.post(
            f"{API_URL}/gerar",
            json={"user_story": user_story, "criterios": criterios, "motor": motor},
            timeout=180,
        )
    except requests.ConnectionError:
        raise RuntimeError(
            "Não foi possível conectar ao backend. Inicie-o com: uvicorn backend.main:app --reload"
        )
    except requests.Timeout:
        raise RuntimeError("O backend demorou demais para responder.")
    if resp.status_code == 200:
        return resp.json()
    detalhe = resp.json().get("detail", resp.text)
    if isinstance(detalhe, list):  # erros de validação do Pydantic
        detalhe = "; ".join(d.get("msg", "").replace("Value error, ", "") for d in detalhe)
    raise RuntimeError(str(detalhe))

# 1. Configuração da Página
st.set_page_config(
    page_title="QA Autonomous",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Função Helper para renderizar Mermaid.js no Streamlit
def render_mermaid(mermaid_code: str):
    """Renderiza código Mermaid via injeção de HTML e Javascript"""
    html_code = f"""
    <div class="mermaid" style="display: flex; justify-content: center; margin-top: 20px;">
        {mermaid_code}
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    """
    components.html(html_code, height=500, scrolling=True)

# 3. Cabeçalho e Barra Lateral
st.title("🤖 QA Autonomous")
st.markdown("**Ferramenta de Geração Automática de Testes com NLP e Model-Based Testing (MBT)**")

with st.sidebar:
    st.header("⚙️ Configurações")
    modelo_selecionado = st.selectbox("Motor LLM", ["Gemini (Cloud)", "Ollama (Local)"])
    st.markdown("---")
    st.info("Fatec Cotia\n\nProjeto: Processamento de Linguagem Natural\n\nAluno: Juan Cezar Yghor Andrade")

# 4. Layout Principal (Entradas e Saídas)
col_input, col_output = st.columns([1, 2], gap="large")

with col_input:
    st.subheader("1. Entradas (Requisitos)")
    
    user_story = st.text_area(
        "User Story",
        value="Como um cliente bancário,\nQuero realizar o login no sistema,\nPara acessar minha conta corrente.",
        height=100
    )
    
    criterios = st.text_area(
        "Critérios de Aceite",
        value="1. Senha correta redireciona para o Dashboard.\n2. Senha incorreta exibe mensagem de erro.\n3. Três tentativas erradas bloqueiam a conta.",
        height=150
    )
    
    gerar_btn = st.button("🚀 Gerar Modelo e Testes", type="primary", use_container_width=True)

with col_output:
    st.subheader("2. Artefatos Gerados (MBT & BDD)")
    
    if gerar_btn:
        try:
            with st.spinner(f"Processando requisitos com {modelo_selecionado}... Extraindo Estados e Transições..."):
                modelo = chamar_backend(user_story, criterios, modelo_selecionado)
        except RuntimeError as e:
            st.error(str(e))
        else:
            tab1, tab2 = st.tabs(["📊 Grafo de Estados (Mermaid)", "🧩 Modelo MBT (JSON)"])

            with tab1:
                st.markdown("Visualização da extração estruturada de nós e transições críticas.")
                render_mermaid(modelo_para_mermaid(modelo))

            with tab2:
                st.json(modelo)
    else:
        st.info("👈 Preencha os requisitos e clique em gerar para visualizar a análise MBT.")
