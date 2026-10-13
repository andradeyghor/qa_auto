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

# ---------------------------------------------------------------- estilo claro (Light Mode)
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0f172a;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1200px 600px at 0% -10%, rgba(99, 102, 241, 0.08), transparent 60%),
        radial-gradient(1000px 500px at 100% 0%, rgba(14, 165, 233, 0.08), transparent 50%),
        #f8fafc;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 1400px; }

/* ---------- hero ---------- */
.hero {
    padding: 28px 32px; border-radius: 20px; margin-bottom: 24px;
    background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
    animation: fadeUp .5s ease both;
}
.hero h1 {
    margin: 0; font-size: 2.3rem; font-weight: 800; letter-spacing: -.02em;
    background: linear-gradient(90deg, #4338ca, #0284c7);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { margin: 6px 0 0; color: #475569; font-size: 1.02rem; }
.stepper { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
.step {
    padding: 6px 14px; border-radius: 999px; font-size: .82rem; font-weight: 600;
    background: #eef2ff; border: 1px solid #c7d2fe; color: #3730a3;
}
.step b { color: #4f46e5; margin-right: 6px; }

/* ---------- cards & cabeçalhos ---------- */
.card-title {
    font-size: 1.05rem; font-weight: 700; color: #0f172a; margin: 4px 0 10px;
    display: flex; align-items: center; gap: 8px;
}
.badge {
    font-size: .72rem; padding: 2px 10px; border-radius: 999px; font-weight: 700;
    background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe;
}
.badge.demo { background: #fef9c3; color: #854d0e; border-color: #fde047; }
.badge.live { background: #dcfce7; color: #166534; border-color: #86efac; }
.badge.time { background: #f1f5f9; color: #334155; border-color: #cbd5e1; }

[data-testid="stTextArea"] textarea {
    background: #ffffff !important; border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important; color: #0f172a !important; line-height: 1.55;
    box-shadow: 0 1px 2px rgba(0,0,0,.03);
    transition: border-color .15s, box-shadow .15s;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important;
}
[data-testid="stTextArea"] label p { font-weight: 600; color: #1e293b; }

/* ---------- botões ---------- */
.stButton > button[kind="primary"], .stDownloadButton > button {
    border: 0; border-radius: 12px; font-weight: 700; padding: .7rem 1.2rem;
    background: linear-gradient(90deg, #4f46e5, #0284c7); color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.28);
    transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px); filter: brightness(1.05);
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.38); color: #ffffff !important;
}

/* ---------- métricas ---------- */
.metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 6px 0 18px; }
.metric {
    padding: 14px 16px; border-radius: 14px; animation: fadeUp .4s ease both;
    background: #ffffff; border: 1px solid #e2e8f0;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
}
.metric .v { font-size: 1.75rem; font-weight: 800; color: #0f172a; line-height: 1.15; }
.metric .l { font-size: .74rem; color: #64748b; text-transform: uppercase; letter-spacing: .05em; margin-top: 4px; font-weight: 600; }
.metric.ok .v { color: #16a34a; }
.metric.warn .v { color: #d97706; }
.metric.info .v { color: #2563eb; }

/* ---------- abas ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 2px solid #e2e8f0; }
.stTabs [data-baseweb="tab"] {
    height: 44px; padding: 0 16px; border-radius: 10px 10px 0 0; font-weight: 600; color: #64748b;
}
.stTabs [aria-selected="true"] { color: #4338ca !important; background: #eef2ff; }
.stTabs [data-baseweb="tab-highlight"] { background: #4f46e5; height: 3px; }

/* ---------- estado vazio ---------- */
.empty {
    text-align: center; padding: 60px 20px; border-radius: 18px;
    background: #ffffff; border: 2px dashed #cbd5e1; color: #64748b; animation: fadeUp .5s ease both;
}
.empty .icon { font-size: 3rem; animation: float 3s ease-in-out infinite; }
.empty h3 { color: #0f172a; margin: 10px 0 4px; font-weight: 700; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}
.about {
    padding: 14px 16px; border-radius: 12px; font-size: .85rem; color: #475569; line-height: 1.6;
    background: #f8fafc; border: 1px solid #e2e8f0;
}
.about b { color: #0f172a; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
@media (max-width: 1000px) { .metrics { grid-template-columns: repeat(2, 1fr); } }
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


def chamar_backend(user_story: str, criterios: str, motor: str, api_key: str | None = None) -> dict:
    """Envia os requisitos ao backend. Lança RuntimeError com mensagem amigável em caso de erro."""
    try:
        payload = {
            "user_story": user_story,
            "criterios": criterios,
            "motor": motor,
        }
        if api_key:
            payload["api_key"] = api_key

        resp = requests.post(
            f"{API_URL}/gerar",
            json=payload,
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


def extrair_requisitos_de_texto(conteudo: str) -> tuple[str, str]:
    """Tenta separar inteligentemente User Story e Critérios de Aceite de um arquivo."""
    linhas = conteudo.strip().splitlines()
    us_linhas, crit_linhas = [], []
    secao_atual = "us"

    for linha in linhas:
        l_lower = linha.strip().lower()
        if "critério" in l_lower or "criterio" in l_lower or "acceptance" in l_lower:
            secao_atual = "crit"
            continue
        if ("user story" in l_lower or "estória" in l_lower or "história" in l_lower) and not crit_linhas:
            secao_atual = "us"
            continue

        if secao_atual == "us":
            us_linhas.append(linha)
        else:
            crit_linhas.append(linha)

    us_final = "\n".join(us_linhas).strip()
    crit_final = "\n".join(crit_linhas).strip()

    if not crit_final:
        # Se não encontrou divisão clara, mantém o texto principal como User Story
        return us_final or conteudo, ""
    return us_final, crit_final


def render_mermaid(mermaid_code: str):
    """Renderiza código Mermaid (tema claro) via HTML + Javascript em iframe isolado."""
    html_code = f"""
    <style>
      body {{ margin: 0; background: transparent; }}
      .box {{ display: flex; justify-content: center; padding: 20px;
              background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0;
              box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
    </style>
    <div class="box"><div class="mermaid">{html.escape(mermaid_code)}</div></div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#e0e7ff',
                primaryTextColor: '#1e1b4b',
                primaryBorderColor: '#6366f1',
                lineColor: '#0284c7',
                fontFamily: 'Inter, sans-serif'
            }}
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

    api_key_custom = None
    if modelo_selecionado == "Gemini (Cloud)":
        api_key_custom = st.text_input(
            "🔑 Chave API Gemini (opcional)",
            type="password",
            placeholder="AIzaSy...",
            help="Se preenchida, substitui temporariamente a GEMINI_API_KEY do arquivo .env.",
        )

    modo_demo = st.toggle(
        "Modo demonstração",
        value=True,
        help="Usa dados de exemplo rápidos, sem backend nem LLM. Desative para chamar a API real.",
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
    badge = '<span class="badge demo">DEMO</span>' if modo_demo else '<span class="badge live">API REAL</span>'
    st.markdown(f'<div class="card-title">📥 Entradas {badge}</div>', unsafe_allow_html=True)

    # 1. Upload de Arquivos
    with st.expander("📂 Importar arquivo (.txt, .md)", expanded=False):
        uploaded_file = st.file_uploader(
            "Selecione um arquivo de requisitos",
            type=["txt", "md"],
            help="Carrega o conteúdo diretamente nos campos de texto abaixo.",
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            try:
                conteudo = uploaded_file.read().decode("utf-8")
                us_ext, crit_ext = extrair_requisitos_de_texto(conteudo)
                if us_ext:
                    st.session_state["user_story"] = us_ext
                if crit_ext:
                    st.session_state["criterios"] = crit_ext
                st.success("Requisitos importados com sucesso! ✨")
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")

    user_story = st.text_area("User Story", key="user_story", height=120)
    criterios = st.text_area("Critérios de Aceite", key="criterios", height=180)
    st.caption(f"{len(user_story)} / 2000 caracteres · {total_criterios(criterios)} critério(s) detectado(s)")
    gerar_btn = st.button("🚀 Gerar Modelo e Testes", type="primary", width="stretch")

if gerar_btn:
    try:
        t0 = time.perf_counter()
        with st.status(f"Processando com {modelo_selecionado}…", expanded=True) as status:
            if modo_demo:
                for msg in (
                    "Analisando User Story e critérios…",
                    "Extraindo estados e transições…",
                    "Validando coerência do grafo…",
                    "Gerando cenários e scripts…",
                ):
                    st.write(f"⏳ {msg}")
                    time.sleep(0.4)
                ex = EXEMPLOS[st.session_state["exemplo"]]
                resultado = {k: ex[k] for k in ("modelo", "gherkin", "pytest")}
            else:
                st.write("⏳ Consultando o backend e o LLM…")
                resultado = {
                    "modelo": chamar_backend(
                        user_story,
                        criterios,
                        modelo_selecionado,
                        api_key=api_key_custom or None,
                    ),
                    "gherkin": None,
                    "pytest": None,
                }
            status.update(label="Análise concluída ✅", state="complete", expanded=False)
        duracao = time.perf_counter() - t0
        resultado["total_criterios"] = total_criterios(criterios)
        resultado["tempo_execucao"] = f"{duracao:.2f}s"
        resultado["motor_usado"] = modelo_selecionado
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
        tempo_ex = res.get("tempo_execucao", "—")
        motor_ex = res.get("motor_usado", modelo_selecionado)

        st.markdown(
            f"""
            <div class="metrics">
              <div class="metric"><div class="v">{len(modelo['estados'])}</div><div class="l">Estados</div></div>
              <div class="metric"><div class="v">{len(modelo['transicoes'])}</div><div class="l">Transições</div></div>
              <div class="metric {'ok' if completo else 'warn'}"><div class="v">{len(cobertos)}/{total}</div>
                  <div class="l">Critérios</div></div>
              <div class="metric info"><div class="v" style="font-size:1.1rem;padding-top:8px">{modelo['inicial']}</div>
                  <div class="l">Inicial</div></div>
              <div class="metric"><div class="v" style="font-size:1.35rem;padding-top:4px">{tempo_ex}</div>
                  <div class="l">Latência ({'Demo' if modo_demo else 'Real'})</div></div>
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
