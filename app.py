import html
import os
import re
import time

import requests
import streamlit as st

from demo_data import EXEMPLOS

API_URL = os.getenv("QA_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="QA Autonomous",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------- estilo
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; }
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(900px 500px at 8% -10%, rgba(124,92,255,.22), transparent 60%),
        radial-gradient(800px 500px at 100% 0%, rgba(34,211,238,.14), transparent 55%),
        #0b1020;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 1400px; }

/* ---------- hero ---------- */
.hero {
    padding: 28px 32px; border-radius: 22px; margin-bottom: 22px;
    background: linear-gradient(135deg, rgba(124,92,255,.25), rgba(34,211,238,.12));
    border: 1px solid rgba(255,255,255,.10);
    box-shadow: 0 10px 40px rgba(0,0,0,.35);
    animation: fadeUp .6s ease both;
}
.hero h1 {
    margin: 0; font-size: 2.4rem; font-weight: 800; letter-spacing: -.02em;
    background: linear-gradient(90deg, #c4b5fd, #67e8f9);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { margin: 6px 0 0; color: #aab2d5; font-size: 1.02rem; }
.stepper { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
.step {
    padding: 6px 14px; border-radius: 999px; font-size: .82rem; font-weight: 600;
    background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.10); color: #c7cdea;
}
.step b { color: #67e8f9; margin-right: 6px; }

/* ---------- cards ---------- */
.card-title {
    font-size: 1.05rem; font-weight: 700; color: #e6e9f5; margin: 4px 0 10px;
    display: flex; align-items: center; gap: 8px;
}
.badge {
    font-size: .7rem; padding: 2px 9px; border-radius: 999px; font-weight: 700;
    background: rgba(124,92,255,.25); color: #c4b5fd; border: 1px solid rgba(124,92,255,.5);
}
.badge.demo { background: rgba(250,204,21,.15); color: #fde68a; border-color: rgba(250,204,21,.4); }
.badge.live { background: rgba(52,211,153,.15); color: #6ee7b7; border-color: rgba(52,211,153,.4); }

[data-testid="stTextArea"] textarea {
    background: rgba(19,26,51,.9) !important; border: 1px solid rgba(255,255,255,.12) !important;
    border-radius: 14px !important; color: #e6e9f5 !important; line-height: 1.55;
    transition: border-color .2s, box-shadow .2s;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: #7c5cff !important; box-shadow: 0 0 0 3px rgba(124,92,255,.25) !important;
}
[data-testid="stTextArea"] label p { font-weight: 600; color: #c7cdea; }

/* ---------- botões ---------- */
.stButton > button[kind="primary"], .stDownloadButton > button {
    border: 0; border-radius: 14px; font-weight: 700; padding: .7rem 1rem;
    background: linear-gradient(90deg, #7c5cff, #22d3ee); color: #fff;
    box-shadow: 0 8px 24px rgba(124,92,255,.35);
    transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px); filter: brightness(1.08);
    box-shadow: 0 12px 30px rgba(124,92,255,.5); color: #fff;
}

/* ---------- métricas ---------- */
.metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 6px 0 18px; }
.metric {
    padding: 16px 18px; border-radius: 16px; animation: fadeUp .5s ease both;
    background: rgba(19,26,51,.85); border: 1px solid rgba(255,255,255,.09);
}
.metric .v { font-size: 1.9rem; font-weight: 800; color: #fff; line-height: 1.1; }
.metric .l { font-size: .78rem; color: #8f98c4; text-transform: uppercase; letter-spacing: .06em; margin-top: 4px; }
.metric.ok .v { color: #6ee7b7; }
.metric.warn .v { color: #fcd34d; }

/* ---------- abas ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid rgba(255,255,255,.08); }
.stTabs [data-baseweb="tab"] {
    height: 44px; padding: 0 16px; border-radius: 12px 12px 0 0; font-weight: 600; color: #8f98c4;
}
.stTabs [aria-selected="true"] { color: #fff !important; background: rgba(124,92,255,.18); }
.stTabs [data-baseweb="tab-highlight"] { background: linear-gradient(90deg, #7c5cff, #22d3ee); height: 3px; }

/* ---------- estado vazio ---------- */
.empty {
    text-align: center; padding: 70px 20px; border-radius: 20px;
    border: 2px dashed rgba(255,255,255,.14); color: #8f98c4; animation: fadeUp .6s ease both;
}
.empty .icon { font-size: 3.2rem; animation: float 3s ease-in-out infinite; }
.empty h3 { color: #e6e9f5; margin: 10px 0 4px; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: #0e1429; border-right: 1px solid rgba(255,255,255,.07); }
.about {
    padding: 14px 16px; border-radius: 14px; font-size: .85rem; color: #aab2d5; line-height: 1.6;
    background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08);
}
.about b { color: #e6e9f5; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
@media (max-width: 900px) { .metrics { grid-template-columns: repeat(2, 1fr); } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- lógica
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
            "Não foi possível conectar ao backend. Inicie-o com: uvicorn backend.main:app --reload "
            "ou ative o **Modo demonstração** na barra lateral."
        )
    except requests.Timeout:
        raise RuntimeError("O backend demorou demais para responder.")
    if resp.status_code == 200:
        return resp.json()
    detalhe = resp.json().get("detail", resp.text)
    if isinstance(detalhe, list):  # erros de validação do Pydantic
        detalhe = "; ".join(d.get("msg", "").replace("Value error, ", "") for d in detalhe)
    raise RuntimeError(str(detalhe))


def total_criterios(texto: str) -> int:
    nums = re.findall(r"^\s*(\d+)\s*[.)\-:]", texto, flags=re.MULTILINE)
    return len(set(nums)) if nums else len([l for l in texto.splitlines() if l.strip()])


def render_mermaid(mermaid_code: str):
    """Renderiza código Mermaid (tema escuro) via HTML + Javascript."""
    html_code = f"""
    <style>
      body {{ margin: 0; background: transparent; }}
      .box {{ display: flex; justify-content: center; padding: 16px;
              background: #131a33; border-radius: 16px; border: 1px solid rgba(255,255,255,.1); }}
    </style>
    <div class="box"><div class="mermaid">{html.escape(mermaid_code)}</div></div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true, theme: 'dark',
            themeVariables: {{ primaryColor: '#2a2f5c', primaryTextColor: '#e6e9f5',
                               primaryBorderColor: '#7c5cff', lineColor: '#67e8f9',
                               fontFamily: 'Inter, sans-serif' }}
        }});
    </script>
    """
    st.iframe(html_code, height=540)


def carregar_exemplo():
    ex = EXEMPLOS[st.session_state["exemplo"]]
    st.session_state["user_story"] = ex["user_story"]
    st.session_state["criterios"] = ex["criterios"]
    st.session_state.pop("resultado", None)


# estado inicial
if "user_story" not in st.session_state:
    nome0 = next(iter(EXEMPLOS))
    st.session_state["exemplo"] = nome0
    st.session_state["user_story"] = EXEMPLOS[nome0]["user_story"]
    st.session_state["criterios"] = EXEMPLOS[nome0]["criterios"]

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    modelo_selecionado = st.selectbox("Motor LLM", ["Gemini (Cloud)", "Ollama (Local)"])
    modo_demo = st.toggle(
        "Modo demonstração", value=True,
        help="Usa dados de exemplo, sem backend nem LLM. Desative para chamar a API real.",
    )
    st.selectbox("📚 Carregar exemplo", list(EXEMPLOS), key="exemplo", on_change=carregar_exemplo)
    st.markdown("---")
    st.markdown(
        '<div class="about"><b>Fatec Cotia</b><br>Processamento de Linguagem Natural<br><br>'
        "<b>Aluno</b><br>Juan Cezar Yghor Andrade</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- hero
st.markdown(
    """
    <div class="hero">
        <h1>🤖 QA Autonomous</h1>
        <p>Geração automática de testes com Processamento de Linguagem Natural e Model-Based Testing.</p>
        <div class="stepper">
            <span class="step"><b>1</b>Requisitos</span>
            <span class="step"><b>2</b>Modelo de estados</span>
            <span class="step"><b>3</b>Cenários BDD</span>
            <span class="step"><b>4</b>Scripts Pytest</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- layout
col_input, col_output = st.columns([1, 2], gap="large")

with col_input:
    badge = '<span class="badge demo">DEMO</span>' if modo_demo else '<span class="badge live">API</span>'
    st.markdown(f'<div class="card-title">📥 Entradas {badge}</div>', unsafe_allow_html=True)

    user_story = st.text_area("User Story", key="user_story", height=120)
    criterios = st.text_area("Critérios de Aceite", key="criterios", height=180)
    st.caption(f"{len(user_story)} / 2000 caracteres · {total_criterios(criterios)} critério(s) detectado(s)")
    gerar_btn = st.button("🚀 Gerar Modelo e Testes", type="primary", width="stretch")

if gerar_btn:
    try:
        with st.status(f"Processando com {modelo_selecionado}…", expanded=True) as status:
            if modo_demo:
                for msg in (
                    "Analisando User Story e critérios…",
                    "Extraindo estados e transições…",
                    "Validando coerência do grafo…",
                    "Gerando cenários e scripts…",
                ):
                    st.write(f"⏳ {msg}")
                    time.sleep(0.6)
                ex = EXEMPLOS[st.session_state["exemplo"]]
                resultado = {k: ex[k] for k in ("modelo", "gherkin", "pytest")}
            else:
                st.write("⏳ Consultando o backend e o LLM…")
                resultado = {"modelo": chamar_backend(user_story, criterios, modelo_selecionado),
                             "gherkin": None, "pytest": None}
            status.update(label="Análise concluída ✅", state="complete", expanded=False)
        resultado["total_criterios"] = total_criterios(criterios)
        st.session_state["resultado"] = resultado
    except RuntimeError as e:
        st.session_state.pop("resultado", None)
        st.error(str(e), icon="🚨")

with col_output:
    st.markdown('<div class="card-title">📦 Artefatos Gerados <span class="badge">MBT &amp; BDD</span></div>',
                unsafe_allow_html=True)
    res = st.session_state.get("resultado")

    if not res:
        st.markdown(
            '<div class="empty"><div class="icon">🧠</div><h3>Nenhuma análise ainda</h3>'
            "Preencha os requisitos à esquerda e clique em <b>Gerar Modelo e Testes</b>.</div>",
            unsafe_allow_html=True,
        )
    else:
        modelo = res["modelo"]
        cobertos = {t["criterio"] for t in modelo["transicoes"] if t.get("criterio") is not None}
        total = res["total_criterios"]
        completo = total > 0 and len(cobertos) >= total
        st.markdown(
            f"""
            <div class="metrics">
              <div class="metric"><div class="v">{len(modelo['estados'])}</div><div class="l">Estados</div></div>
              <div class="metric"><div class="v">{len(modelo['transicoes'])}</div><div class="l">Transições</div></div>
              <div class="metric {'ok' if completo else 'warn'}"><div class="v">{len(cobertos)}/{total}</div>
                  <div class="l">Critérios cobertos</div></div>
              <div class="metric"><div class="v" style="font-size:1.15rem;padding-top:8px">{modelo['inicial']}</div>
                  <div class="l">Estado inicial</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["📊 Grafo", "🔀 Transições", "📝 BDD (Gherkin)", "💻 Pytest", "🧩 JSON"]
        )
        with tab1:
            render_mermaid(modelo_para_mermaid(modelo))
        with tab2:
            linhas = [
                {"De": t["de"], "Evento": t["evento"], "Para": t["para"],
                 "Critério": f"#{t['criterio']}" if t.get("criterio") is not None else "—"}
                for t in modelo["transicoes"]
            ]
            st.dataframe(linhas, width="stretch", hide_index=True)
        with tab3:
            if res["gherkin"]:
                st.code(res["gherkin"], language="gherkin")
                st.download_button("⬇️ Baixar .feature", data=res["gherkin"],
                                   file_name="cenarios.feature", mime="text/plain")
            else:
                st.info("A geração de cenários Gherkin será adicionada em breve.", icon="🚧")
        with tab4:
            if res["pytest"]:
                st.code(res["pytest"], language="python")
                st.download_button("⬇️ Baixar test_cenarios.py", data=res["pytest"],
                                   file_name="test_cenarios.py", mime="text/x-python")
            else:
                st.info("A geração de scripts Pytest será adicionada em breve.", icon="🚧")
        with tab5:
            st.json(modelo)
