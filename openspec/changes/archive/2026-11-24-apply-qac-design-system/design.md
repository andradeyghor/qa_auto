# Design

## Context

- A interface inteira está em `app.py` (Streamlit 1.65): `st.set_page_config` com emoji, um bloco `CSS` com ~120 linhas de estilo índigo/degradê, um hero em HTML, métricas em HTML (`.metrics`), abas e botões com emojis no rótulo, e `render_mermaid` com `themeVariables` índigo.
- O tema nativo vem de `.streamlit/config.toml` (`primaryColor #4f46e5`, fundo `#f8fafc`).
- O kit está em `assets/QUALITY ASSURANCE CONSULTANT/QUALITY ASSURANCE CONSULTANT/` (pasta aninhada, nome com espaços) e traz `README.md` com instruções de aplicação, `tokens.css`/`tokens.json`, e os grupos `assets/Logos` e `assets/Icones`.
- `tests/test_interface.py` usa `AppTest` e localiza elementos por `key` (`gerar`, `executar`, `user_story`…), não por rótulo — trocar rótulos e ícones não quebra os testes existentes.
- Requisitos: ver `specs/identidade-visual/spec.md`.

## Goals / Non-Goals

**Goals:**
- Um único ponto de verdade para os valores de cor/fonte/espaço dentro do `app.py`, espelhando `tokens.css`.
- Testes automatizados que travem nome, ausência da marca provisória, ícones proibidos e rótulos de status.

**Non-Goals:**
- Tema escuro ou alternância de tema.
- Componentes Streamlit customizados (React) ou CSS externo servido por arquivo.
- Mudar a estrutura dos artefatos gerados pelo backend: só o nome da marca é trocado nos textos (docstrings, `LEIAME.md`, título da API, descrição da CLI).

## Decisions

1. **Copiar os arquivos do kit para `assets/` na raiz, com os mesmos nomes** (`assets/qac-logo-horizontal-claro.svg`, `assets/qac-icone-escuro.svg`, `assets/qac-favicon-32.png`, etc.), como o README do kit pede. Alternativa: referenciar o caminho aninhado com espaços — rejeitada por ser frágil e não seguir a instrução do kit. A pasta original do kit permanece como fonte.
   - Caminhos resolvidos a partir de `Path(__file__).parent / "assets"` para funcionar tanto com `streamlit run app.py` quanto com `AppTest.from_file` (que roda de outro cwd).

2. **Tokens como dicionário Python + CSS gerado por f-string.** Um `TOKENS = {"bg": "#FFFFFF", "surface": "#F4F4F4", "border": "#D4D4D4", "text": "#111111", "text-secondary": "#4A4A4A", "text-muted": "#6B6B6B", "brand": "#FFC72C", "brand-strong": "#D9A400", "on-brand": "#111111", "status-success": "#15803D", "status-error": "#B42318"}` alimenta o CSS, o Mermaid e o badge de status. Alternativa: injetar `tokens.css` lido do disco — rejeitada porque o kit gera o arquivo com tema escuro e classes que não usamos, e o dicionário permite testar a paleta sem parsear CSS. Os valores são copiados de `tokens.json` uma vez; a seção de risco cobre divergência.

3. **CSS reescrito do zero, não remendado.** O bloco atual é removido por completo e substituído pelo trecho do README do kit, ampliado para: hero sem degradê (fundo `bg`, título em `display` com `letter-spacing .04em`, tagline em `text-muted`), cards/métricas em `surface` com borda `border` e `radius-md` (10px), badges em estilo `label` (12px/600/caixa alta) com `radius-sm`, abas ativas com sublinhado `accent-ink` (#111111), código em JetBrains Mono, e espaçamentos só da escala (4/8/12/16/24/32/48). Sem sombras coloridas e sem animações `float`/`fadeUp` (o kit não as define).
   - Botões de download (`.stDownloadButton`) passam de "primário em degradê" para estilo secundário.
   - O amarelo aparece só em: botão primário, barra de progresso, sublinhado decorativo do hero (se usado) e badge DEMO (fundo `brand` com texto `on-brand`). O badge "API REAL" vira neutro (`surface` + borda), já que verde é reservado a status de teste.

4. **Tema nativo via `.streamlit/config.toml`** com o bloco do kit, incluindo `borderColor = "#D4D4D4"` e `linkColor = "#111111"` (suportados no 1.65). O CSS cobre o que o tema não alcança (botão primário amarelo — `primaryColor` fica preto de propósito, para não haver texto branco sobre amarelo nos controles nativos).

5. **Ícones Material Symbols nos parâmetros `icon=`** e no texto via `:material/nome:`. Mapa proposto:
   | Lugar | Antes | Depois |
   | --- | --- | --- |
   | Configurações (sidebar) | ⚙️ | `:material/tune:` |
   | Carregar exemplo / Sistema alvo / Estratégia | 📚 🎯 🧭 | `:material/menu_book:`, `:material/target:`, `:material/route:` |
   | Chave API | 🔑 | `:material/key:` |
   | Entradas / Artefatos | 📥 📦 | `:material/edit_note:`, `:material/inventory_2:` |
   | Importar arquivo / importação ok / erro | 📂 ✨ 📄 | `:material/upload_file:`, `:material/check_circle:`, `:material/error:` |
   | Gerar | 🚀 | `:material/play_arrow:` |
   | Executar | ▶️ | `:material/play_circle:` |
   | Downloads | ⬇️ 📦 | `:material/download:` |
   | Abas | 📊 🧠 🔀 📝 💻 📈 🧩 | `:material/account_tree:`, `:material/notes:`, `:material/swap_horiz:`, `:material/description:`, `:material/code:`, `:material/donut_large:`, `:material/data_object:` |
   | Alertas demo / esqueleto / erro / aviso | 🎬 🧱 🚨 ✋ ⚠️ | `:material/slideshow:`, `:material/construction:`, `:material/error:`, `:material/block:`, `:material/warning:` |
   | Estado vazio | 🧠 | logo símbolo do pato (`qac-simbolo-claro.svg`) |
   | Nuvem (provedor) | ☁️ | `:material/cloud:` |
   A aba "Análise" troca 🧠 (proibido) por ícone neutro. Emojis em `st.write` do status de processamento (⏳) saem; o próprio `st.status` já mostra o spinner.

6. **Status de teste:** `tabela_cenarios` passa a produzir "APROVADO"/"FALHOU". Para a cor, usar `st.dataframe(...).style` não é necessário: aplicar `column_config` não colore texto, então a tabela usa `pandas.Styler` com `color` de `status-success`/`status-error` na coluna Resultado. Alternativa mais simples considerada: badges HTML — rejeitada porque perde ordenação/rolagem do dataframe. O texto garante a leitura mesmo que a cor não seja aplicada. Vereditos usam o texto do backend acrescido da contagem (`len(execucao.bug.falhas)`): "Bug detectado em N teste(s)".
   - `RESULTADO_TENTATIVA` (✅/❌/⏱️) vira "VÁLIDO"/"INVÁLIDO"/"TIMEOUT" pelo mesmo princípio.

7. **Métricas:** manter o grid HTML atual (o kit não proíbe), recolorido: valor em `text`, rótulo em estilo `label`/`text-muted`; o destaque "critérios completos" usa `status-success` com o texto já presente ("N/N"), e incompleto usa `text` com um badge "PARCIAL" — o âmbar (`#d97706`) e o azul atuais saem por não serem tokens.

8. **Mermaid:** `themeVariables` com `primaryColor #F4F4F4`, `primaryBorderColor #111111`, `primaryTextColor #111111`, `lineColor #4A4A4A`, `fontFamily Inter`; caixa com borda `#D4D4D4`, `radius-md`, sem sombra.

9. **Ajustes da verificação visual (durante a implementação):**
   - *Logo horizontal embutido no HTML.* No `<img>` do `st.logo` a Inter da página não carrega, e o nome saía cortado. Além disso, o texto do próprio SVG do kit passa ~27 unidades do `viewBox` mesmo com a Inter. Com a barra expandida, o SVG do kit é embutido sem alterações no topo da barra, com `overflow: visible` e 210px de largura (acima do mínimo de 160px). O `st.logo` continua sendo chamado, fica oculto na barra por CSS e mostra o ícone com a barra recolhida.
   - *Seletores de botão por descendente* (`.stButton button[kind=primary]`), porque um botão com `help=` fica dentro de um tooltip e o seletor de filho direto não o alcança.
   - *Resultado como primeira coluna* nas tabelas de execução: nomes longos de cenário empurravam APROVADO/FALHOU para fora da área visível.
   - *Cores dos alertas pelo tema* (`blueColor`/`blueBackgroundColor`/`blueTextColor` em neutros do kit; `green*`/`red*` nas cores de status), para o `st.info` não usar o azul padrão. O `st.warning` mantém a cor nativa, porque o kit não define cor de aviso.

## Risks / Trade-offs

- [Valores do kit duplicados em `TOKENS` podem divergir de `tokens.json` se o kit for atualizado] → teste que carrega `tokens.json` do kit e compara as cores do tema claro com `TOKENS`.
- [Seletores CSS internos do Streamlit (`data-testid`, `kind="primary"`) mudam entre versões] → limitar o CSS a seletores já usados hoje e aos do README do kit; verificação visual manual ao final.
- [O SVG horizontal usa texto em Inter "ao vivo"; se a fonte não carregar dentro do `<img>` do `st.logo`, o nome cai para a fonte de reserva] → aceitável no app web (o kit documenta isso); não converter em curvas nesta mudança.
- [Google Fonts indisponível offline] → as pilhas de reserva do kit (`Helvetica Neue, Arial` / `ui-monospace, Consolas`) ficam na declaração.
- [Ícone Material inexistente renderiza como texto cru] → usar apenas nomes conferidos no catálogo Material Symbols e checar visualmente cada tela.

## Migration Plan

Mudança só de apresentação, sem dados ou API afetados. Rollback = reverter o commit (`app.py`, `.streamlit/config.toml`, `assets/qac-*`, `README.md`, testes).
