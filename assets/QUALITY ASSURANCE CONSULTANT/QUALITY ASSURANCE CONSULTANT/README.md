# QUALITY ASSURANCE CONSULTANT

De requisitos a testes executáveis.

Sistema de design do QUALITY ASSURANCE CONSULTANT, ferramenta que transforma User Stories e Critérios de Aceite em cenários Gherkin e testes Pytest, com cobertura medida e verificação contra um bug injetado. O app é feito em Streamlit, com interface em português. Este pacote substitui a identidade provisória "QA Autonomous" (emoji de robô e tema índigo).

## Para quem vai atualizar a UI (leia primeiro)

Ao aplicar este sistema no app:

1. Troque o nome em todo lugar: `page_title`, títulos e README do repositório passam a ser **QUALITY ASSURANCE CONSULTANT**. O nome provisório "QA Autonomous" e o emoji 🤖 saem por completo.
2. Baixe os arquivos dos grupos **Logos** e **Icones** desta página e salve-os numa pasta `assets/` na raiz do projeto, com os mesmos nomes.
3. Substitua o tema em `.streamlit/config.toml` pelo bloco da seção "Tema do Streamlit".
4. Aplique o `st.set_page_config`, o `st.logo` e o CSS da seção "Código do app".
5. Revise telas com resultado de teste: aprovado usa `status-success`, falha usa `status-error`, sempre com texto ou ícone junto, nunca só a cor.
6. Não invente cores, fontes ou espaçamentos: use apenas os tokens deste sistema.

## Voz e conteúdo

- Tom de consultor experiente: direto, preciso, com bom humor leve. Nada de exagero ou "mágica de IA".
- Interface em português do Brasil. Termos técnicos consagrados ficam em inglês: User Story, Gherkin, Pytest, bug.
- Rótulos curtos e no imperativo: "Gerar testes", "Executar no sistema com bug", "Baixar cenários".
- Vereditos claros e verificáveis: "12 de 12 transições cobertas", "Bug detectado em 3 testes".
- O nome da marca aparece sempre em caixa alta: QUALITY ASSURANCE CONSULTANT. A sigla QA é aceita em espaços curtos.

## Logo

O símbolo é um pato de borracha de perfil, virado para a direita, com chapéu fedora e a asa desenhada como um check. O pato remete ao *rubber duck debugging*, o chapéu ao consultor e o check ao teste aprovado.

| Arquivo | Uso |
| --- | --- |
| `qac-logo-horizontal-claro.svg` | Cabeçalho e sidebar em fundo claro, README, slides |
| `qac-logo-horizontal-escuro.svg` | Fundo escuro (já vem com fundo `#111111`) |
| `qac-simbolo-claro.svg` / `qac-simbolo-escuro.svg` | Só o pato, para espaços médios |
| `qac-icone-escuro.svg` / `qac-icone-claro.svg` | Ícone de app e avatar |
| `qac-icone-512.png` | Ícone em PNG para redes e `page_icon` |
| `qac-favicon-32.png` | Favicon e `page_icon` do Streamlit |

Regras do logo:

- Área livre ao redor igual a `space-12` (48px) na versão horizontal.
- Largura mínima da versão horizontal: 160px. Abaixo disso, use o ícone.
- Em fundo escuro, sempre a versão escura (chapéu claro).
- Não mude cores, não gire, não vire o pato para a esquerda, não troque o chapéu, não aplique sombra ou degradê.
- O texto dos SVGs horizontais usa Inter instalada no sistema; para impressão ou uso fora da web, converta o texto em curvas.

## Cores

A base é neutra (branco, preto e cinzas) e o amarelo é a única cor de marca. Proporção: cerca de 70% `bg` e `surface`, 20% `text` e superfícies escuras, 10% `brand`.

- `brand` (#FFC72C) é para fundos e destaques, nunca para texto sobre `bg` claro.
- Texto sobre `brand` ou `brand-strong` usa sempre `on-brand` (#111111).
- `status-success` e `status-error` existem só para resultados de teste. Vermelho nunca aparece como decoração ou cor de marca.
- `accent-ink` é a cor de controles do Streamlit (`primaryColor`): preto no tema claro. Isso evita texto branco sobre amarelo nos componentes nativos.

## Tipografia

Inter (Google Fonts) para tudo; JetBrains Mono para Gherkin, Pytest e JSON. Títulos em peso 700 ou 800; o nome da marca em caixa alta com espaçamento leve (estilo `display`). Escala completa em Tipografia.

## Tema do Streamlit

Substitua o conteúdo de `.streamlit/config.toml` por:

```toml
[theme]
base = "light"
primaryColor = "#111111"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F4F4F4"
textColor = "#111111"
font = "sans serif"
```

Para um tema escuro, use `base = "dark"`, `primaryColor = "#FFC72C"`, `backgroundColor = "#111111"`, `secondaryBackgroundColor = "#2B2B2B"` e `textColor = "#FFFFFF"`. Se a versão do Streamlit no projeto aceitar `borderColor` e `linkColor`, use `#D4D4D4` e `#111111` no tema claro.

## Código do app

No início do `app.py`:

```python
import streamlit as st

st.set_page_config(
    page_title="QUALITY ASSURANCE CONSULTANT",
    page_icon="assets/qac-favicon-32.png",
    layout="wide",
)

st.logo(
    "assets/qac-logo-horizontal-claro.svg",
    icon_image="assets/qac-icone-escuro.svg",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400&display=swap');
html, body, [class*="css"] { font-family: Inter, "Helvetica Neue", Arial, sans-serif; }
code, pre { font-family: "JetBrains Mono", ui-monospace, Menlo, monospace; }
.stButton > button[kind="primary"] { background: #FFC72C; color: #111111; border: 0; border-radius: 10px; font-weight: 600; }
.stButton > button[kind="primary"]:hover { background: #D9A400; color: #111111; }
.stButton > button[kind="secondary"] { border: 1px solid #D4D4D4; border-radius: 10px; color: #111111; }
.stProgress > div > div > div > div { background-color: #FFC72C; }
</style>
""", unsafe_allow_html=True)
```

Use `type="primary"` só na ação principal de cada etapa (por exemplo, "Gerar testes"). As demais ações ficam como botão secundário.

## Componentes e padrões

- **Botão primário:** fundo `brand`, texto `on-brand`, raio `radius-md`, padding `space-3` × `space-4`; hover `brand-strong`.
- **Botão secundário:** fundo transparente, borda `border`, texto `text`.
- **Card / painel:** fundo `surface`, borda `border`, raio `radius-md`, padding `space-4`.
- **Bloco de código (Gherkin, Pytest):** estilo `code`, fundo `surface`, raio `radius-sm`.
- **Veredito:** badge com estilo `label`; aprovado = texto `status-success` com "APROVADO", falha = texto `status-error` com "FALHOU". Sempre com palavra, nunca só cor.
- **Espaçamento:** `space-8` entre seções, `space-4` entre campos, `space-12` no topo da página.

## Iconografia

Use ícones de traço simples (Material Symbols, que o Streamlit já aceita no formato `:material/check_circle:`). Proibido: robôs, lupas, insetos, cérebros e faíscas de "IA". O único personagem da marca é o pato.
