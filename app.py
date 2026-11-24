import base64
import hashlib
import html
import json
import os
import re
import time
from pathlib import Path

import requests
import streamlit as st

from backend.entrada import (
    ErroImportacao,
    extrair_requisitos_de_texto,
    numerar_criterios,
    total_criterios,
    validar_entrada,
)
from backend.execucao import (
    BUG_DETECTADO,
    BUG_NAO_DETECTADO,
    ERRO_EXECUCAO,
    MODELO_DIVERGE,
    Execucao,
    ResultadoVariante,
    executar_testes,
)
from backend.caminhos import ESTRATEGIAS, formatar_valor
from backend.geracao import SLUG_LIVRE, Artefatos, gerar_artefatos
from backend.provedores import REGISTRO as PROVEDORES
from backend.schemas import MAX_CARACTERES, criterios_cobertos, estado_inicial
from backend.servico import espera_maxima
from demo_data import EXEMPLOS, modelo_de_referencia
from sistemas_exemplo import SISTEMAS

API_URL = os.getenv("QA_API_URL", "http://localhost:8000")

ASSETS = Path(__file__).resolve().parent / "assets"
MARCA = "QUALITY ASSURANCE CONSULTANT"
TAGLINE = "De requisitos a testes executáveis."
LOGO = ASSETS / "qac-logo-horizontal-claro.svg"
LOGO_ESCURO = ASSETS / "qac-logo-horizontal-escuro.svg"
ICONE = ASSETS / "qac-icone-escuro.svg"
SIMBOLO = ASSETS / "qac-simbolo-claro.svg"
SIMBOLO_ESCURO = ASSETS / "qac-simbolo-escuro.svg"
FAVICON = ASSETS / "qac-favicon-32.png"

# Tokens de cor do tema claro do design kit (assets/QUALITY ASSURANCE CONSULTANT/.../tokens.json).
TOKENS = {
    "bg": "#FFFFFF",
    "surface": "#F4F4F4",
    "border": "#D4D4D4",
    "text": "#111111",
    "text-secondary": "#4A4A4A",
    "text-muted": "#6B6B6B",
    "brand": "#FFC72C",
    "brand-strong": "#D9A400",
    "on-brand": "#111111",
    "accent-ink": "#111111",
    "status-success": "#15803D",
    "status-error": "#B42318",
}
# Tokens do tema escuro (coluna "dark" do tokens.json); as cores de marca não têm variante escura.
TOKENS_ESCURO = {
    **TOKENS,
    "bg": "#111111",
    "surface": "#2B2B2B",
    "border": "#4A4A4A",
    "text": "#FFFFFF",
    "text-secondary": "#D4D4D4",
    "text-muted": "#BDBDBD",
    "accent-ink": "#FFFFFF",
    "status-success": "#4ADE80",
    "status-error": "#F97066",
}

st.set_page_config(
    page_title=MARCA,
    page_icon=str(FAVICON),
    layout="wide",
    initial_sidebar_state="expanded",
)
# O st.logo mostra a imagem num <img>, onde a Inter da página não carrega: sem Inter instalada, o nome do
# logo horizontal sai cortado. Por isso, com a barra expandida, o logo é o SVG do kit embutido no HTML
# (logo_horizontal, abaixo); o st.logo fica oculto na barra e mostra o ícone quando ela é recolhida.
st.logo(str(LOGO), icon_image=str(ICONE), size="large")


def svg_data_uri(caminho: Path) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(caminho.read_bytes()).decode("ascii")


def logo_horizontal() -> str:
    """SVGs do logo horizontal do kit (claro e escuro), sem alterações, embutidos no HTML para usar a Inter
    da página; o CSS mostra a versão do tema ativo."""
    return (
        f'<div class="qac-logo qac-so-claro" role="img" aria-label="{MARCA}">{LOGO.read_text(encoding="utf-8")}</div>'
        f'<div class="qac-logo qac-so-escuro" role="img" aria-label="{MARCA}">'
        f'{LOGO_ESCURO.read_text(encoding="utf-8")}</div>'
    )


def simbolo_pato() -> str:
    """Símbolo do pato do kit nas versões clara e escura; o CSS mostra a do tema ativo."""
    return (
        f'<img class="qac-so-claro" src="{svg_data_uri(SIMBOLO)}" alt="">'
        f'<img class="qac-so-escuro" src="{svg_data_uri(SIMBOLO_ESCURO)}" alt="">'
    )


# ---------------------------------------------------------------- estilo (design kit, temas claro e escuro)
def _variaveis(tokens: dict) -> str:
    return "\n".join(f"    --qac-{nome}: {valor};" for nome, valor in tokens.items())


# Palpite do servidor para o primeiro desenho; o script de tema (SCRIPT_TEMA) confirma ou corrige no navegador.
_PALPITE_ESCURO = (
    ':root:not([data-qac-tema="claro"]) {\n' + _variaveis(TOKENS_ESCURO) + "\n}"
    if st.context.theme.type == "dark" else ""
)
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400&display=swap');
:root {
__VARIAVEIS__
    --qac-font-sans: Inter, "Helvetica Neue", Arial, sans-serif;
    --qac-font-mono: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace;
}
__PALPITE__
:root[data-qac-tema="escuro"] {
__VARIAVEIS_ESCURO__
}

/* ---------- elementos por tema ---------- */
.qac-so-escuro { display: none !important; }
:root[data-qac-tema="escuro"] .qac-so-claro { display: none !important; }
:root[data-qac-tema="escuro"] .qac-so-escuro { display: block !important; }
__PALPITE_ELEMENTOS__

html, body, [class*="css"], .stApp { font-family: var(--qac-font-sans); color: var(--qac-text); }
code, pre, .stCode, [data-testid="stCode"] * { font-family: var(--qac-font-mono) !important; font-size: 14px; line-height: 20px; }
[data-testid="stAppViewContainer"] { background: var(--qac-bg); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 48px; max-width: 1400px; }
/* o elemento do script de tema não tem conteúdo visível; sem isto, o espaçamento entre elementos soma 16px */
[data-testid="stElementContainer"]:has(> [data-testid="stHtml"] > script:only-child) { display: none; }

/* ---------- logo (largura mínima de 160px para a versão horizontal) ---------- */
[data-testid="stSidebarHeader"] [data-testid="stSidebarLogo"] { display: none; }
.qac-logo { margin: -32px 0 32px; }
/* o texto do SVG do kit passa um pouco do viewBox; overflow visível evita o corte sem alterar o arquivo */
.qac-logo svg { display: block; width: 210px; height: auto; overflow: visible; }
/* o logo escuro traz fundo próprio (token bg escuro): o contêiner usa o mesmo fundo e vira uma placa */
.qac-logo.qac-so-escuro { background: var(--qac-bg); border-radius: 10px; padding: 8px 12px; width: fit-content; }
.qac-logo.qac-so-escuro svg { width: 186px; }

/* ---------- cabeçalho ---------- */
.hero { padding: 0 0 32px; margin-bottom: 32px; border-bottom: 1px solid var(--qac-border); }
.hero h1 {
    margin: 0; padding: 0; font: 800 40px/44px var(--qac-font-sans); letter-spacing: .04em;
    color: var(--qac-text); text-transform: uppercase;
}
.hero p { margin: 8px 0 0; color: var(--qac-text-muted); font: 400 16px/24px var(--qac-font-sans); }
.stepper { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
.step {
    padding: 4px 12px; border-radius: 6px; font: 600 12px/16px var(--qac-font-sans); letter-spacing: .06em;
    text-transform: uppercase; background: var(--qac-surface); border: 1px solid var(--qac-border);
    color: var(--qac-text-secondary);
}
.step b { color: var(--qac-text); margin-right: 4px; }

/* ---------- cards & cabeçalhos ---------- */
.card-title {
    font: 700 24px/32px var(--qac-font-sans); color: var(--qac-text); margin: 0 0 16px;
    display: flex; align-items: center; gap: 8px;
}
.badge {
    font: 600 12px/16px var(--qac-font-sans); letter-spacing: .06em; text-transform: uppercase;
    padding: 2px 8px; border-radius: 6px;
    background: var(--qac-surface); color: var(--qac-text-secondary); border: 1px solid var(--qac-border);
}
.badge.demo { background: var(--qac-brand); color: var(--qac-on-brand); border-color: var(--qac-brand); }

[data-testid="stTextArea"] textarea {
    background: var(--qac-bg) !important; border: 1px solid var(--qac-border) !important;
    border-radius: 10px !important; color: var(--qac-text) !important; font: 400 16px/24px var(--qac-font-sans);
}
[data-testid="stTextArea"] textarea:focus { border-color: var(--qac-accent-ink) !important; }
[data-testid="stTextArea"] label p { font-weight: 600; color: var(--qac-text); }

/* ---------- botões ---------- */
.stButton button[kind="primary"] {
    background: var(--qac-brand); color: var(--qac-on-brand); border: 0; border-radius: 10px;
    font-weight: 600; padding: 12px 16px;
}
.stButton button[kind="primary"]:hover, .stButton button[kind="primary"]:focus:not(:active) {
    background: var(--qac-brand-strong); color: var(--qac-on-brand); border: 0;
}
.stButton button[kind="secondary"], .stDownloadButton button {
    background: transparent; border: 1px solid var(--qac-border); border-radius: 10px;
    color: var(--qac-text); font-weight: 600;
}
.stButton button[kind="secondary"]:hover, .stDownloadButton button:hover {
    border-color: var(--qac-text); color: var(--qac-text); background: transparent;
}
.stProgress > div > div > div > div { background-color: var(--qac-brand); }

/* ---------- métricas ---------- */
.metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin: 0 0 24px; }
.metric {
    padding: 16px; border-radius: 10px; background: var(--qac-surface); border: 1px solid var(--qac-border);
}
.metric .v { font: 800 28px/36px var(--qac-font-sans); color: var(--qac-text); }
.metric .v.pequeno { font: 700 18px/26px var(--qac-font-sans); padding-top: 6px; }
.metric .l {
    font: 600 12px/16px var(--qac-font-sans); letter-spacing: .06em; text-transform: uppercase;
    color: var(--qac-text-muted); margin-top: 4px;
}
.metric.ok .v { color: var(--qac-status-success); }
.metric .badge { margin-left: 4px; vertical-align: middle; }

/* ---------- abas ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--qac-border); }
.stTabs [data-baseweb="tab"] { height: 44px; padding: 0 16px; font-weight: 600; color: var(--qac-text-muted); }
.stTabs [aria-selected="true"] { color: var(--qac-text) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--qac-accent-ink); height: 2px; }

/* ---------- estado vazio ---------- */
.empty {
    text-align: center; padding: 48px 24px; border-radius: 16px;
    background: var(--qac-surface); border: 1px dashed var(--qac-border); color: var(--qac-text-muted);
}
.empty img { width: 96px; height: auto; margin: 0 auto; }

/* ---------- resultado da execução ---------- */
.qac-status { width: 100%; border-collapse: collapse; font: 400 14px/20px var(--qac-font-sans); }
.qac-status th {
    text-align: left; padding: 8px; color: var(--qac-text-muted); border-bottom: 1px solid var(--qac-border);
    font: 600 12px/16px var(--qac-font-sans); letter-spacing: .06em; text-transform: uppercase;
}
.qac-status td { padding: 8px; border-bottom: 1px solid var(--qac-border); color: var(--qac-text); vertical-align: top; }
.qac-status td.ok, .qac-status td.falha { font-weight: 600; white-space: nowrap; }
.qac-status td.ok { color: var(--qac-status-success); }
.qac-status td.falha { color: var(--qac-status-error); }
.empty h3 { color: var(--qac-text); margin: 16px 0 4px; font: 600 18px/26px var(--qac-font-sans); }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: var(--qac-surface); border-right: 1px solid var(--qac-border); }
.about {
    padding: 16px; border-radius: 10px; font: 400 14px/20px var(--qac-font-sans); color: var(--qac-text-secondary);
    background: var(--qac-bg); border: 1px solid var(--qac-border);
}
.about b { color: var(--qac-text); }

@media (max-width: 1000px) { .metrics { grid-template-columns: repeat(2, 1fr); } }
</style>
"""
CSS = (
    CSS.replace("__VARIAVEIS_ESCURO__", _variaveis(TOKENS_ESCURO))
    .replace("__VARIAVEIS__", _variaveis(TOKENS))
    .replace("__PALPITE__", _PALPITE_ESCURO)
    .replace("__PALPITE_ELEMENTOS__", (
        ':root:not([data-qac-tema="claro"]) .qac-so-claro { display: none !important; }\n'
        ':root:not([data-qac-tema="claro"]) .qac-so-escuro { display: block !important; }'
    ) if _PALPITE_ESCURO else "")
)
st.markdown(CSS, unsafe_allow_html=True)

# Detecta o tema ativo pelo fundo do app e marca o <html> com data-qac-tema="claro"|"escuro". O Streamlit não
# avisa o Python quando o usuário troca o tema no menu, então o CSS próprio segue esse atributo.
SCRIPT_TEMA = """
<script>
(() => {
  if (window.__qacTema) { window.__qacTema(); return; }
  const raiz = document.documentElement;
  const luminancia = (cor) => {
    const m = (cor || "").match(/\\d+(\\.\\d+)?/g);
    if (!m || m.length < 3) return null;
    if (m.length > 3 && Number(m[3]) === 0) return null;  // fundo transparente
    const [r, g, b] = m.slice(0, 3).map(Number);
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  };
  const detectar = () => {
    const app = document.querySelector('[data-testid="stApp"]') || document.body;
    let l = luminancia(getComputedStyle(app).backgroundColor);
    if (l === null) l = window.matchMedia("(prefers-color-scheme: dark)").matches ? 0 : 1;
    const tema = l < 0.5 ? "escuro" : "claro";
    if (raiz.dataset.qacTema !== tema) raiz.dataset.qacTema = tema;
  };
  window.__qacTema = detectar;
  detectar();
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", detectar);
  new MutationObserver(detectar).observe(document.head, { childList: true, subtree: true, characterData: true });
  setInterval(detectar, 500);
})();
</script>
"""
st.html(SCRIPT_TEMA, unsafe_allow_javascript=True)


# ---------------------------------------------------------------- lógica
AVISO_DEMO = "Demonstração: modelo de referência, sem LLM"
LEGENDA_TEMA = ":material/contrast: Tema claro ou escuro: menu ⋮ no canto superior direito."
MENSAGENS_STATUS = {
    422: "Requisição inválida",
    500: "Erro interno no servidor",
    502: "Falha no provedor de LLM",
    504: "Tempo esgotado no servidor",
}


def mensagem_de_erro(resp) -> str:
    """Mensagem legível para qualquer resposta de erro, com ou sem corpo JSON."""
    try:
        corpo = resp.json()
    except ValueError:
        corpo = None
    mensagem = None
    if isinstance(corpo, dict):
        mensagem = corpo.get("mensagem") or corpo.get("detail")
        if isinstance(mensagem, list):
            mensagem = "; ".join(str(d.get("msg", d)) for d in mensagem)
    if not mensagem:
        mensagem = MENSAGENS_STATUS.get(resp.status_code, "Erro no servidor")
    return f"{mensagem} (status {resp.status_code})"


def chamar_backend(
    user_story: str,
    criterios: str,
    motor: str,
    api_key: str | None = None,
    sistema: str | None = None,
    modelo: str | None = None,
) -> dict:
    """Envia os requisitos ao backend e devolve o corpo da resposta.

    Lança RuntimeError com mensagem legível em qualquer falha, sem expor exceções ao usuário.
    """
    payload = {"user_story": user_story, "criterios": criterios, "motor": motor, "sistema": sistema}
    if modelo:
        payload["modelo"] = modelo
    if api_key:
        payload["api_key"] = api_key
    try:
        resp = requests.post(f"{API_URL}/gerar", json=payload, timeout=espera_maxima())
    except requests.ConnectionError:
        raise RuntimeError(
            "O backend está indisponível. Inicie-o com: `uvicorn backend.main:app --reload` "
            "ou ative o **Modo demonstração** na barra lateral."
        )
    except requests.Timeout:
        raise RuntimeError(f"O backend não respondeu em {espera_maxima()}s.")
    except requests.RequestException as e:
        raise RuntimeError(f"Falha na comunicação com o backend: {e}")
    if resp.status_code != 200:
        raise RuntimeError(mensagem_de_erro(resp))
    try:
        corpo = resp.json()
        corpo["modelo"]
    except (ValueError, KeyError, TypeError):
        raise RuntimeError("O backend devolveu uma resposta em formato inesperado.")
    return corpo


def exemplo_sem_edicao(nome_exemplo: str, user_story: str, criterios: str) -> bool:
    exemplo = EXEMPLOS[nome_exemplo]
    return (user_story.strip(), criterios.strip()) == (exemplo["user_story"].strip(), exemplo["criterios"].strip())


def identificacao(nome_exemplo: str, user_story: str, criterios: str) -> tuple[str, str | None]:
    """Slug e título dos artefatos: os do exemplo, se o texto não foi editado; senão, os de texto livre."""
    if exemplo_sem_edicao(nome_exemplo, user_story, criterios):
        exemplo = EXEMPLOS[nome_exemplo]
        return exemplo["sistema"] or exemplo["gabarito"], nome_exemplo
    return SLUG_LIVRE, None


def motivo_recusa_demo(nome_exemplo: str, user_story: str, criterios: str) -> str | None:
    """Na demonstração, só exemplos com modelo de referência e sem edição podem ser exibidos."""
    if not exemplo_sem_edicao(nome_exemplo, user_story, criterios):
        return (
            f"O texto na tela não corresponde ao exemplo “{nome_exemplo}”: ele foi editado ou digitado. "
            "A demonstração só exibe exemplos sem edição. "
            "Desative o **Modo demonstração** para processar texto livre."
        )
    if modelo_de_referencia(nome_exemplo) is None:
        return (
            f"O exemplo “{nome_exemplo}” ainda não tem modelo de referência, então não pode ser exibido "
            "na demonstração. Desative o **Modo demonstração** para gerá-lo com o LLM."
        )
    return None


def importar_arquivo(arquivo) -> None:
    """Preenche os campos só quando o arquivo muda, para que edições posteriores prevaleçam."""
    if arquivo is None:
        st.session_state.pop("arquivo_importado", None)
        st.session_state.pop("importacao", None)
        return
    dados = arquivo.getvalue()
    assinatura = f"{arquivo.name}:{hashlib.sha256(dados).hexdigest()}"
    if st.session_state.get("arquivo_importado") == assinatura:
        return
    st.session_state["arquivo_importado"] = assinatura
    try:
        historia, criterios_importados = extrair_requisitos_de_texto(dados.decode("utf-8-sig"))
    except UnicodeDecodeError:
        st.session_state["importacao"] = ("erro", "O arquivo precisa estar em UTF-8.")
        return
    except ErroImportacao as e:
        st.session_state["importacao"] = ("erro", str(e))
        return
    st.session_state["user_story"] = historia
    st.session_state["criterios"] = criterios_importados
    st.session_state.pop("resultado", None)
    st.session_state.pop("execucao", None)
    st.session_state["importacao"] = ("ok", f"Requisitos importados de {arquivo.name}.")


def render_mermaid(mermaid_code: str):
    """Renderiza código Mermaid via HTML + Javascript em iframe, com a paleta do kit do tema ativo.

    O iframe (srcdoc) tem a mesma origem do app: lê o data-qac-tema do <html> do app e redesenha quando muda.
    """
    def paleta(t: dict) -> dict:
        return {"bg": t["bg"], "border": t["border"], "variaveis": {
            "background": t["bg"], "primaryColor": t["surface"], "primaryTextColor": t["text"],
            "primaryBorderColor": t["text"], "secondaryColor": t["brand"], "tertiaryColor": t["bg"],
            "lineColor": t["text-secondary"], "textColor": t["text"],
            "fontFamily": 'Inter, "Helvetica Neue", Arial, sans-serif',
        }}

    def em_script(valor) -> str:  # JSON seguro dentro de <script>
        return json.dumps(valor, ensure_ascii=False).replace("</", "<\\/")

    paletas = {"claro": paleta(TOKENS), "escuro": paleta(TOKENS_ESCURO)}
    html_code = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
      body {{ margin: 0; background: transparent; }}
      .box {{ display: flex; justify-content: center; padding: 24px; border-radius: 10px;
              border: 1px solid {TOKENS['border']}; background: {TOKENS['bg']}; }}
    </style>
    <div class="box"><div id="diagrama"></div></div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        const paletas = {em_script(paletas)};
        const codigo = {em_script(mermaid_code)};
        const caixa = document.querySelector('.box');
        const destino = document.getElementById('diagrama');
        let atual = null, n = 0;
        const temaDoApp = () => {{
            try {{
                return window.parent.document.documentElement.dataset.qacTema === 'escuro' ? 'escuro' : 'claro';
            }} catch (e) {{
                return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'escuro' : 'claro';
            }}
        }};
        async function desenhar() {{
            const tema = temaDoApp();
            if (tema === atual) return;
            atual = tema;
            const p = paletas[tema];
            caixa.style.background = p.bg;
            caixa.style.borderColor = p.border;
            mermaid.initialize({{ startOnLoad: false, theme: 'base', themeVariables: p.variaveis }});
            const {{ svg }} = await mermaid.render('qac-diagrama-' + (n++), codigo);
            destino.innerHTML = svg;
        }}
        desenhar();
        try {{
            new MutationObserver(desenhar).observe(window.parent.document.documentElement,
                {{ attributes: true, attributeFilter: ['data-qac-tema'] }});
        }} catch (e) {{}}
    </script>
    """
    st.iframe(html_code, height=540)


RESULTADO_TENTATIVA = {"valido": "VÁLIDO", "invalido": "INVÁLIDO", "timeout": "TIMEOUT"}
APROVADO, FALHOU = "APROVADO", "FALHOU"
CATEGORIA_VARIAVEL = {"estado": "Estado (muda por ações)", "entrada": "Entrada (vem com o evento)",
                      "contexto": "Contexto (fixa no cenário)"}


def render_analise(modelo: dict, historico: list[dict]):
    """Análise do LLM, variáveis do modelo e tentativas da extração."""
    st.markdown("**Análise dos critérios**")
    st.write(modelo.get("analise") or "—")
    st.markdown("**Variáveis**")
    if modelo.get("variaveis"):
        st.dataframe(
            [
                {"Nome": v["nome"], "Tipo": v["tipo"], "Categoria": CATEGORIA_VARIAVEL.get(v["categoria"], v["categoria"]),
                 "Valor inicial": "—" if v.get("valor_inicial") is None else str(v["valor_inicial"])}
                for v in modelo["variaveis"]
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("O modelo não declara variáveis: contagens são representadas por estados.")
    if historico:
        st.markdown("**Tentativas da extração**")
        st.dataframe(
            [
                {"Tentativa": i, "Resultado": RESULTADO_TENTATIVA.get(t["resultado"], t["resultado"]),
                 "Duração": f"{t['duracao']:.1f}s", "Erros": t.get("erro") or "—"}
                for i, t in enumerate(historico, start=1)
            ],
            width="stretch",
            hide_index=True,
        )


def render_codigo(titulo: str | None, codigo: str, linguagem: str, nome_arquivo: str, mime: str):
    """Código de um artefato com o botão de download do arquivo."""
    if titulo:
        st.markdown(f"**{titulo}**")
    st.code(codigo, language=linguagem)
    st.download_button(f"Baixar {nome_arquivo}", data=codigo, file_name=nome_arquivo, mime=mime,
                       key=f"baixar_{nome_arquivo}", icon=":material/download:")


def _valores(pares) -> str:
    return ", ".join(f"{nome} = {formatar_valor(valor)}" for nome, valor in pares) or "—"


def render_cobertura(modelo: dict, artefatos: Artefatos):
    """Cobertura de estados, transições e critérios, pendências com motivo e a rastreabilidade de cada caminho."""
    cobertura = artefatos.cobertura
    colunas = st.columns(4)
    for coluna, (rotulo, par) in zip(colunas, (("Estados", cobertura.estados), ("Transições", cobertura.transicoes),
                                               ("Critérios", cobertura.criterios))):
        coluna.metric(rotulo, f"{cobertura.percentual(par)}%", help=f"{par[0]} de {par[1]} cobertos")
    colunas[3].metric("Caminhos", cobertura.caminhos, help=f"{cobertura.caminhos_de_borda} cenário(s) de borda")
    st.caption(cobertura.resumo())
    for aviso in cobertura.avisos:
        st.warning(aviso, icon=":material/warning:")
    if cobertura.nao_cobertos:
        st.markdown("**Não cobertos**")
        st.dataframe([{"Tipo": i.tipo, "Item": i.nome, "Motivo": i.motivo} for i in cobertura.nao_cobertos],
                     width="stretch", hide_index=True)
    if cobertura.bordas_omitidas:
        st.markdown("**Bordas não geradas**")
        st.dataframe([{"Comparação": i.nome, "Motivo": i.motivo} for i in cobertura.bordas_omitidas],
                     width="stretch", hide_index=True)
    if not (cobertura.nao_cobertos or cobertura.bordas_omitidas):
        st.caption(":material/check_circle: Todos os estados, transições e critérios do modelo foram cobertos.")
    transicoes = modelo["transicoes"]
    st.markdown("**Caminhos**")
    st.dataframe(
        [
            {
                "Cenário": f"Caminho {n}" + (" (borda)" if c.borda else ""),
                "Transições": " → ".join(transicoes[p.transicao]["id"] if p.aceito else "recusa" for p in c.passos),
                "Contexto": _valores(c.contexto),
                "Entradas": "; ".join(f"{p.evento}: {_valores(p.dados)}" for p in c.passos if p.dados) or "—",
                "Critérios": ", ".join(map(str, c.criterios(modelo))) or "—",
                "Final": c.final,
            }
            for n, c in enumerate(artefatos.caminhos, start=1)
        ],
        width="stretch",
        hide_index=True,
    )


def nome_sistema(sistema_id: str) -> str:
    return SISTEMAS[sistema_id].nome if sistema_id else "Nenhum (gerar só esqueleto)"


def carregar_exemplo():
    ex = EXEMPLOS[st.session_state["exemplo"]]
    st.session_state["user_story"] = ex["user_story"]
    st.session_state["criterios"] = ex["criterios"]
    st.session_state["sistema_alvo"] = ex["sistema"] or ""
    st.session_state.pop("resultado", None)
    st.session_state.pop("execucao", None)


def tabela_cenarios(resultado: ResultadoVariante) -> str:
    """Tabela HTML com a palavra APROVADO/FALHOU de cada cenário. A cor vem das variáveis CSS de status, então
    acompanha o tema ativo sem rerun (um st.dataframe estilizado no Python ficaria com as cores do tema antigo)."""
    linhas = "".join(
        f'<tr><td class="{"ok" if c.passou else "falha"}">{APROVADO if c.passou else FALHOU}</td>'
        f"<td>{html.escape(c.nome)}</td></tr>"
        for c in resultado.cenarios
    )
    return f'<table class="qac-status"><thead><tr><th>Resultado</th><th>Cenário</th></tr></thead><tbody>{linhas}</tbody></table>'


def render_falhas(titulo: str, resultado: ResultadoVariante):
    if resultado.falhas:
        linhas = [f"- **{c.nome}:** {c.motivo}" for c in resultado.falhas]
        st.markdown(f"**Falhas no {titulo}**\n" + "\n".join(linhas))


def render_execucao(execucao: Execucao):
    if execucao.veredito == ERRO_EXECUCAO:
        motivo = execucao.correto.erro or execucao.bug.erro
        st.error(f"**{ERRO_EXECUCAO}:** {motivo}", icon=":material/error:")
        return
    if execucao.veredito == BUG_DETECTADO:
        n = len(execucao.bug.falhas)
        st.success(
            f"**{BUG_DETECTADO} em {n} teste{'s' if n != 1 else ''}:** "
            "os testes passam no sistema correto e falham no sistema com bug.",
            icon=":material/check_circle:",
        )
    elif execucao.veredito == BUG_NAO_DETECTADO:
        st.warning(f"**{BUG_NAO_DETECTADO}:** os testes passam nas duas variantes, então são insuficientes.",
                   icon=":material/warning:")
    elif execucao.veredito == MODELO_DIVERGE:
        st.warning(f"**{MODELO_DIVERGE}:** há testes falhando no sistema correto. Revise o modelo gerado.",
                   icon=":material/warning:")

    col_correto, col_bug = st.columns(2)
    with col_correto:
        st.markdown("**Sistema correto**")
        st.markdown(tabela_cenarios(execucao.correto), unsafe_allow_html=True)
    with col_bug:
        st.markdown("**Sistema com bug**")
        if execucao.bug.erro:
            st.caption(f"Sem resultado: {execucao.bug.erro}")
        else:
            st.markdown(tabela_cenarios(execucao.bug), unsafe_allow_html=True)
    render_falhas("sistema correto", execucao.correto)
    render_falhas("sistema com bug", execucao.bug)


# estado inicial
if "user_story" not in st.session_state:
    nome0 = next(iter(EXEMPLOS))
    st.session_state["exemplo"] = nome0
    st.session_state["user_story"] = EXEMPLOS[nome0]["user_story"]
    st.session_state["criterios"] = EXEMPLOS[nome0]["criterios"]
    st.session_state["sistema_alvo"] = EXEMPLOS[nome0]["sistema"] or ""

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(logo_horizontal(), unsafe_allow_html=True)
    st.markdown("### :material/tune: Configurações")
    provedor_id = st.selectbox(
        "Motor LLM", list(PROVEDORES), key="provedor", format_func=lambda i: PROVEDORES[i].nome
    )
    provedor = PROVEDORES[provedor_id]
    modelo_selecionado = provedor.nome
    modelo_llm = st.text_input(
        "Modelo (opcional)",
        key="modelo_llm",
        placeholder=provedor.modelo_padrao() or "defina OPENAI_COMPAT_MODEL",
        help="Vazio usa o modelo configurado no .env para este provedor.",
    )
    if provedor.nuvem:
        st.caption(":material/cloud: Este provedor roda na nuvem: os requisitos digitados serão enviados a ele.")

    api_key_custom = None
    if provedor_id == "gemini":
        api_key_custom = st.text_input(
            ":material/key: Chave API Gemini (opcional)",
            type="password",
            placeholder="AIzaSy...",
            help="Se preenchida, substitui temporariamente a GEMINI_API_KEY do arquivo .env.",
        )

    modo_demo = st.toggle(
        "Modo demonstração",
        value=True,
        help="Usa dados de exemplo rápidos, sem backend nem LLM. Desative para chamar a API real.",
    )
    st.selectbox(":material/menu_book: Carregar exemplo", list(EXEMPLOS), key="exemplo", on_change=carregar_exemplo)
    st.selectbox(
        ":material/track_changes: Sistema alvo",
        [*SISTEMAS, ""],
        key="sistema_alvo",
        format_func=nome_sistema,
        help="Sistema contra o qual os testes rodam. Sem sistema, os artefatos são apenas esqueletos.",
    )
    st.selectbox(
        ":material/route: Estratégia de caminhos",
        list(ESTRATEGIAS),
        key="estrategia",
        format_func=ESTRATEGIAS.get,
        help="Todas as transições: poucos caminhos que, juntos, percorrem cada transição. Caminhos elementares: "
        "busca em profundidade que não repete estado nem valores das variáveis de estado.",
    )
    st.checkbox(
        "Cenários de borda",
        value=True,
        key="bordas",
        help="Para cada comparação das guardas, um cenário na fronteira e outro com o primeiro valor fora dela.",
    )
    st.caption(LEGENDA_TEMA)
    st.markdown("---")
    st.markdown(
        '<div class="about"><b>Fatec Cotia</b><br>Processamento de Linguagem Natural<br><br>'
        "<b>Aluno</b><br>Juan Cezar Yghor Andrade</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- hero
st.markdown(
    f"""
    <div class="hero">
        <h1>{MARCA}</h1>
        <p>{TAGLINE} User Stories e Critérios de Aceite viram modelo de estados, cenários Gherkin e testes Pytest.</p>
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
    st.markdown(f'<div class="card-title">Entradas {badge}</div>', unsafe_allow_html=True)

    # 1. Upload de Arquivos
    with st.expander("Importar arquivo (.txt, .md)", expanded=False, icon=":material/upload_file:"):
        st.caption("Use as seções `# História` e `# Critérios`.")
        uploaded_file = st.file_uploader(
            "Selecione um arquivo de requisitos",
            type=["txt", "md"],
            key="arquivo",
            help="Carrega o conteúdo nos campos abaixo. Edições feitas depois prevalecem.",
            label_visibility="collapsed",
        )
        importar_arquivo(uploaded_file)
        if "importacao" in st.session_state:
            situacao, texto = st.session_state["importacao"]
            if situacao == "ok":
                st.success(texto, icon=":material/check_circle:")
            else:
                st.error(texto, icon=":material/error:")

    user_story = st.text_area("User Story", key="user_story", height=120)
    criterios = st.text_area("Critérios de Aceite", key="criterios", height=180)
    criterios_numerados = numerar_criterios(criterios)
    st.caption(
        f"História: {len(user_story.strip())}/{MAX_CARACTERES} · "
        f"Critérios: {len(criterios_numerados)}/{MAX_CARACTERES} caracteres · "
        f"{total_criterios(criterios)} critério(s)"
    )
    if criterios_numerados:
        renumerado = criterios_numerados != "\n".join(l.strip() for l in criterios.splitlines() if l.strip())
        with st.expander("Critérios numerados (como serão enviados)", expanded=renumerado,
                         icon=":material/format_list_numbered:"):
            # "1\." evita que o Markdown renumere a lista e esconda a numeração real
            st.markdown("  \n".join(re.sub(r"^(\d+)\.", r"\1\\.", l) for l in criterios_numerados.splitlines()))
    gerar_btn = st.button("Gerar testes", key="gerar", type="primary", width="stretch",
                          icon=":material/play_arrow:")

if gerar_btn:
    st.session_state.pop("execucao", None)
    st.session_state.pop("resultado", None)
    sistema_alvo = st.session_state["sistema_alvo"] or None
    nome_exemplo = st.session_state["exemplo"]
    erros_entrada = validar_entrada(user_story, criterios_numerados)
    recusa = motivo_recusa_demo(nome_exemplo, user_story, criterios) if modo_demo and not erros_entrada else None
    with col_output:
        if erros_entrada:
            st.error("\n\n".join(erros_entrada), icon=":material/block:")
        elif recusa:
            st.warning(recusa, icon=":material/slideshow:")
        else:
            try:
                t0 = time.perf_counter()
                with st.status(f"Processando com {modelo_selecionado}…", expanded=True) as status:
                    if modo_demo:
                        for msg in (
                            "Carregando o modelo de referência do exemplo…",
                            "Gerando cenários e scripts…",
                        ):
                            st.write(msg)
                            time.sleep(0.3)
                        modelo_gerado = modelo_de_referencia(nome_exemplo)
                        tentativas, duracao_backend, historico = None, None, []
                    else:
                        st.write("Consultando o backend e o LLM…")
                        resposta = chamar_backend(
                            user_story,
                            criterios_numerados,
                            provedor_id,
                            api_key=api_key_custom or None,
                            sistema=sistema_alvo,
                            modelo=modelo_llm.strip() or None,
                        )
                        modelo_gerado = resposta["modelo"]
                        tentativas, duracao_backend = resposta.get("tentativas"), resposta.get("duracao")
                        historico = resposta.get("historico") or []
                        if resposta.get("modelo_llm"):
                            modelo_selecionado = f"{provedor.nome} · {resposta['modelo_llm']}"
                    status.update(label="Análise concluída", state="complete", expanded=False)
                duracao = time.perf_counter() - t0
                slug, titulo = identificacao(nome_exemplo, user_story, criterios)
                st.session_state["resultado"] = {
                    "modelo": modelo_gerado,
                    "artefatos": gerar_artefatos(
                        modelo_gerado, sistema_alvo, slug=slug, titulo=titulo,
                        estrategia=st.session_state["estrategia"], bordas=st.session_state["bordas"],
                    ),
                    "sistema": sistema_alvo,
                    "demo": modo_demo,
                    "total_criterios": total_criterios(criterios_numerados),
                    "tempo_execucao": f"{duracao:.2f}s",
                    "motor_usado": modelo_selecionado,
                    "tentativas": tentativas,
                    "duracao_backend": duracao_backend,
                    "historico": historico,
                }
            except RuntimeError as e:
                st.error(str(e), icon=":material/error:")

with col_output:
    st.markdown('<div class="card-title">Artefatos gerados <span class="badge">MBT &amp; BDD</span></div>',
                unsafe_allow_html=True)
    res = st.session_state.get("resultado")

    if not res:
        st.markdown(
            f'<div class="empty">{simbolo_pato()}<h3>Nenhuma análise ainda</h3>'
            "Preencha os requisitos à esquerda e clique em <b>Gerar testes</b>.</div>",
            unsafe_allow_html=True,
        )
    else:
        modelo = res["modelo"]
        cobertos = criterios_cobertos(modelo)
        total = res["total_criterios"]
        completo = total > 0 and len(cobertos) >= total
        tempo_ex = res.get("tempo_execucao", "—")
        motor_ex = res.get("motor_usado", modelo_selecionado)

        st.markdown(
            f"""
            <div class="metrics">
              <div class="metric"><div class="v">{len(modelo['estados'])}</div><div class="l">Estados</div></div>
              <div class="metric"><div class="v">{len(modelo['transicoes'])}</div><div class="l">Transições</div></div>
              <div class="metric {'ok' if completo else ''}"><div class="v">{len(cobertos)}/{total}</div>
                  <div class="l">Critérios{'' if completo else ' <span class="badge">PARCIAL</span>'}</div></div>
              <div class="metric"><div class="v pequeno">{estado_inicial(modelo)}</div>
                  <div class="l">Inicial</div></div>
              <div class="metric"><div class="v pequeno">{tempo_ex}</div>
                  <div class="l">Latência ({'Demo' if res['demo'] else 'Real'})</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if res.get("tentativas"):
            st.caption(
                f"Backend: {res['tentativas']} tentativa(s) em {res['duracao_backend']:.1f}s com {motor_ex}."
            )

        artefatos = res["artefatos"]
        if res["sistema"]:
            if st.button("Executar testes", key="executar", type="primary", icon=":material/play_circle:",
                         help="Roda os testes no sistema correto e no sistema com bug."):
                with st.spinner("Executando os testes…"):
                    st.session_state["execucao"] = executar_testes(artefatos)
            if "execucao" in st.session_state:
                render_execucao(st.session_state["execucao"])
        else:
            st.info(
                "Sem sistema alvo, os artefatos são esqueletos: os testes falham até o adaptador "
                f"({artefatos.nome_adaptador}) ser implementado.",
                icon=":material/construction:",
            )
        st.download_button(
            f"Baixar pacote ({artefatos.nome_zip})", data=artefatos.zip(), file_name=artefatos.nome_zip,
            mime="application/zip", key="baixar_zip", icon=":material/download:",
            help="Feature, teste, adaptador, conftest, modelo, diagrama, cobertura e instruções (LEIAME.md).",
        )

        abas = st.tabs([":material/account_tree: Grafo", ":material/notes: Análise",
                        ":material/swap_horiz: Transições", ":material/description: BDD (Gherkin)",
                        ":material/code: Pytest", ":material/donut_large: Cobertura", ":material/data_object: JSON"])
        if res["demo"]:
            for aba in abas:
                with aba:
                    st.info(AVISO_DEMO, icon=":material/slideshow:")
        tab1, tab_analise, tab2, tab3, tab4, tab_cobertura, tab5 = abas
        with tab1:
            codigo_mermaid = artefatos.diagrama.rstrip("\n")
            render_mermaid(codigo_mermaid)
            with st.expander("Código Mermaid (stateDiagram-v2)", icon=":material/code:"):
                st.code(codigo_mermaid, language="text")
            st.download_button(f"Baixar {artefatos.nome_diagrama}", data=artefatos.diagrama,
                               file_name=artefatos.nome_diagrama, mime="text/plain", key="baixar_mmd",
                               icon=":material/download:")
        with tab_analise:
            render_analise(modelo, res.get("historico") or [])
        with tab2:
            linhas = [
                {"Id": t["id"], "De": t["de"], "Evento": t["evento"], "Guarda": t.get("guarda") or "—",
                 "Ações": "; ".join(t.get("acoes") or []) or "—", "Para": t["para"],
                 "Critérios": ", ".join(f"#{n}" for n in t.get("criterios") or []) or "—"}
                for t in modelo["transicoes"]
            ]
            st.dataframe(linhas, width="stretch", hide_index=True)
        with tab3:
            render_codigo(None, artefatos.feature, "gherkin", artefatos.nome_feature, "text/plain")
        with tab4:
            render_codigo("Teste (pytest-bdd)", artefatos.script, "python", artefatos.nome_script, "text/x-python")
            render_codigo("Adaptador do sistema sob teste", artefatos.adaptador, "python", artefatos.nome_adaptador,
                          "text/x-python")
            with st.expander("conftest.py e instruções"):
                st.code(artefatos.conftest, language="python")
                st.markdown(artefatos.leiame)
        with tab_cobertura:
            render_cobertura(modelo, artefatos)
        with tab5:
            st.json(modelo)
            st.download_button(f"Baixar {artefatos.nome_modelo}", data=artefatos.modelo_json,
                               file_name=artefatos.nome_modelo, mime="application/json", key="baixar_json",
                               icon=":material/download:")
