# Design

## Context

- O tema nativo vem de `.streamlit/config.toml`. Hoje ele tem só `[theme]` com os valores claros e as cores de alerta (`blue*`, `green*`, `red*`). O Streamlit 1.65 aceita as seções `[theme.light]` e `[theme.dark]` (e `.sidebar` de cada uma). Com as duas definidas, o menu ⋮ (itens System, Light e Dark) oferece Light, Dark e System, e a escolha fica salva no navegador.
- O CSS próprio do `app.py` é gerado a partir de `TOKENS` (só os valores claros) como variáveis `--qac-*` em `:root`. Fora do CSS, há cores fixas do tema claro em dois lugares: `render_mermaid` (paleta passada ao Mermaid dentro de um iframe `srcdoc`) e `tabela_cenarios` (`pandas.Styler` com as cores de status).
- O logo da barra lateral e o pato do estado vazio são SVGs claros embutidos no HTML. O `st.logo` fica oculto na barra expandida e mostra o ícone (`qac-icone-escuro.svg`, fundo `#111111` e chapéu claro) com a barra recolhida.
- Do kit: o logo horizontal escuro traz um retângulo de fundo `#111111` embutido (680×200); o símbolo escuro não tem fundo. Os tokens escuros estão em `tokens.json` (coluna `dark`).
- `st.context.theme.type` existe, mas a própria documentação avisa que pode estar errado na primeira carga e logo após trocar o tema no menu. Também não há API para *mudar* o tema pelo código (por isso não há botão; ver proposal.md).
- `st.html(..., unsafe_allow_javascript=True)` roda JavaScript no documento principal. O `AppTest` não executa JavaScript.

## Goals / Non-Goals

**Goals:**
- O CSS próprio, os logos, o diagrama e as cores de status acompanham o tema ativo, inclusive quando o usuário troca no menu com resultado na tela, sem rerun nem recarga.
- Uma única fonte de valores: `TOKENS` (claro) e `TOKENS_ESCURO` (escuro), conferidos por teste contra o `tokens.json` do kit.

**Non-Goals:**
- Botão de tema dentro do app.
- Mudar cores de componentes nativos além do que o tema do `config.toml` controla (por exemplo, o destaque de sintaxe do `st.code` segue o tema nativo do Streamlit).

## Decisions

1. **Dois temas nativos no `config.toml`.** `[theme]` guarda só o que é comum (`font`). `[theme.light]` recebe o bloco atual. `[theme.dark]` recebe os valores escuros do kit: `base = "dark"`, `primaryColor #FFC72C`, `backgroundColor #111111`, `secondaryBackgroundColor #2B2B2B`, `textColor #FFFFFF`, `borderColor #4A4A4A`, `linkColor #FFFFFF`, e as cores de alerta (`blueColor #FFFFFF`, `blueBackgroundColor #2B2B2B`, `blueTextColor #FFFFFF`, `greenColor`/`greenTextColor #4ADE80`, `redColor`/`redTextColor #F97066`). Alternativa: só `base = "dark"` em `[theme]`, rejeitada porque perderia o tema claro.

2. **Detecção do tema no navegador e um atributo no `<html>`.** Um `st.html` com JavaScript, instalado uma vez por página (marca `window.__qacTema`), lê a cor de fundo computada do app (`[data-testid="stApp"]`). Se a luminância for menor que 0,5, grava `data-qac-tema="escuro"` em `document.documentElement`; senão, `"claro"`. A checagem se repete a cada mudança de `matchMedia('(prefers-color-scheme: dark)')`, num `MutationObserver` sobre o `<head>` (o Streamlit injeta estilos novos ao trocar o tema) e, como reserva, num intervalo de 500 ms. Gravar só quando o valor muda.
   - O CSS segue o padrão do `tokens.css` do kit: `:root { variáveis claras }` e `:root[data-qac-tema="escuro"] { variáveis escuras }`.
   - Contra o "piscar" antes de o script rodar: se `st.context.theme.type == "dark"`, o Python também emite as variáveis escuras em `:root:not([data-qac-tema="claro"])`. Com isso, o palpite inicial do servidor vale até o script confirmar ou corrigir.
   - Alternativas: (a) só `st.context.theme.type`, rejeitada por estar documentadamente errado nas trocas e por não disparar rerun; (b) só `@media (prefers-color-scheme: dark)`, rejeitada porque ignora a escolha manual de Light/Dark no menu.

3. **Logo e símbolo por tema, ambos embutidos.** A barra lateral recebe os dois SVGs (`qac-logo-horizontal-claro.svg` e `...-escuro.svg`) com as classes `qac-so-claro` e `qac-so-escuro`; o CSS mostra um ou outro conforme `data-qac-tema`. O mesmo vale para o pato do estado vazio (`qac-simbolo-claro`/`-escuro`). O logo escuro traz o próprio fundo `#111111`, que sobre a barra `#2B2B2B` apareceria como um retângulo solto. Sem alterar o arquivo, o contêiner do logo escuro recebe o mesmo fundo `#111111`, cantos `radius-md` e `padding` de 8px × 12px. O retângulo do SVG se funde ao contêiner e vira uma placa intencional. O `overflow: visible` do SVG continua valendo para o texto que passa do `viewBox`, e o excesso cai dentro do `padding` da placa.
   - O ícone do `st.logo` continua `qac-icone-escuro.svg` nos dois temas: quadrado escuro com chapéu claro, legível no cabeçalho claro e no escuro.

4. **Tabelas de status em HTML com classes, no lugar do `pandas.Styler`.** As cores do Styler são calculadas no Python e não acompanham a troca de tema sem rerun. `tabela_cenarios` passa a gerar uma tabela HTML (`<table class="qac-status">`) com a palavra APROVADO/FALHOU numa célula de classe `ok`/`falha`, colorida por `var(--qac-status-success)` e `var(--qac-status-error)`. Os nomes de cenário passam por `html.escape` e quebram linha, o que também resolve o corte de nomes longos. Alternativa: `Styler` com `st.context.theme.type`, rejeitada pelo atraso documentado (o FALHOU `#B42318` sobre `#111111` fica com contraste abaixo de 3:1). Efeito colateral: as duas tabelas de execução deixam de ser `st.dataframe`, então os testes que as liam como dataframe passam a ler o markdown.

5. **Mermaid com as duas paletas.** O iframe `srcdoc` tem a mesma origem do app. O script do iframe lê `window.parent.document.documentElement.dataset.qacTema`, escolhe a paleta (`TOKENS` ou `TOKENS_ESCURO`, serializadas em JSON no HTML) e renderiza com `mermaid.render`. Um `MutationObserver` no `<html>` do app refaz a renderização quando o atributo muda. O fundo do iframe acompanha (`bg` do tema).

6. **Legenda de tema.** `st.sidebar.caption(":material/contrast: Tema claro ou escuro: menu ⋮ no canto superior direito.")`, logo abaixo das configurações, antes do bloco "Fatec Cotia".

## Risks / Trade-offs

- [O seletor `[data-testid="stApp"]` ou a forma como o Streamlit injeta estilos muda numa versão futura] → o intervalo de 500 ms cobre a falta do observer; se o seletor sumir, o script cai no `prefers-color-scheme` do sistema. Teste manual na verificação visual.
- [JavaScript desligado ou bloqueado] → o CSS fica no palpite do servidor (`st.context.theme`) ou no claro. Os componentes nativos continuam certos, porque são do Streamlit.
- [Logo escuro com placa `#111111` sobre a barra `#2B2B2B`] → assumido como placa com cantos arredondados; a alternativa (barra lateral `#111111` via `[theme.dark.sidebar]`) contrariaria o token `surface` do kit.
- [O `AppTest` não roda JavaScript nem troca o tema] → testes automáticos cobrem config, tokens, CSS gerado e marcação (classes e os dois logos). A troca real é conferida no Chrome headless, com `prefers-color-scheme: dark` emulado e com a troca pelo menu ⋮.

## Migration Plan

Mudança só de apresentação. Quem não mexer no menu passa a ver o tema do sistema: num sistema escuro, o app abre escuro na primeira visita. Rollback = reverter o commit.
