# Tasks

## 1. Temas nativos

- [x] 1.1 Reorganizar `.streamlit/config.toml` em `[theme]` (só `font`), `[theme.light]` (valores claros atuais, incluindo as cores de alerta) e `[theme.dark]` (valores escuros do kit do design.md, decisão 1); atualizar `test_tema_do_streamlit_do_kit` para ler o arquivo com `tomllib` e conferir as duas seções; verificar que o teste passa e que `streamlit run app.py` sobe sem aviso de opção inválida

## 2. Tokens e CSS por tema

- [x] 2.1 Adicionar `TOKENS_ESCURO` em `app.py` com os valores escuros de `tokens.json` (as chaves sem variante escura repetem o claro); adicionar teste que compara `TOKENS_ESCURO` com a coluna `dark` do kit e verificar que passa
- [x] 2.2 Gerar o CSS com `:root { claras }` e `:root[data-qac-tema="escuro"] { escuras }`, mais o palpite do servidor (`:root:not([data-qac-tema="claro"])` com as escuras quando `st.context.theme.type == "dark"`); revisar o CSS para que nenhuma regra use cor fixa fora das variáveis; verificar com teste que o CSS contém os dois blocos com todos os tokens e que não há cor hexadecimal fora das declarações de variável
- [x] 2.3 Incluir o script de detecção (`st.html(..., unsafe_allow_javascript=True)`, decisão 2): grava `data-qac-tema` no `<html>` a partir da luminância do fundo do app, reage a `matchMedia`, `MutationObserver` no `<head>` e intervalo de 500 ms, e é instalado uma vez; verificar com teste `AppTest` que o app roda sem exceção e que o script está na página, e conferir no Chrome headless que o atributo muda para `escuro` com `prefers-color-scheme: dark` emulado

## 3. Logos, status e diagrama

- [x] 3.1 Embutir as versões clara e escura do logo horizontal na barra lateral e do símbolo no estado vazio, com as classes `qac-so-claro`/`qac-so-escuro` e a placa `#111111` do logo escuro (decisão 3); verificar com teste que a barra lateral contém os dois SVGs do kit sem alteração e que o estado vazio contém os dois símbolos
- [x] 3.2 Trocar `tabela_cenarios` por tabela HTML com classes `ok`/`falha` coloridas por variável CSS e nomes escapados (decisão 4); ajustar `test_status_aprovado_e_falhou` e `test_executar_mostra_veredito_e_nova_geracao_descarta` para ler as tabelas do markdown; verificar com testes que o sistema correto só tem APROVADO, o com bug tem FALHOU, e que um nome de cenário com `<` aparece escapado
- [x] 3.3 Fazer `render_mermaid` embutir as duas paletas e escolher pela `data-qac-tema` do app, re-renderizando quando o atributo muda (decisão 5); verificar com teste que o HTML gerado contém os valores de `TOKENS` e `TOKENS_ESCURO` e nenhuma cor índigo/azul antiga

## 4. Legenda e documentação

- [x] 4.1 Adicionar a legenda ":material/contrast: Tema claro ou escuro: menu ⋮ no canto superior direito." na barra lateral; verificar com teste `AppTest` que a legenda aparece em `app.caption`
- [x] 4.2 Documentar no `README.md`, na seção de execução, que o app segue o tema do sistema e que a troca fica no menu ⋮ (itens System, Light e Dark); verificar lendo a seção

## 5. Verificação final

- [x] 5.1 Rodar `pytest` completo e verificar que toda a suíte passa
- [x] 5.2 No Chrome headless (CDP), conferir o tema escuro com `prefers-color-scheme: dark`: fundo `#111111`, barra e cards `#2B2B2B`, logo e pato escuros, botão primário amarelo com texto escuro, secundários com borda `#4A4A4A`, diagrama escuro e APROVADO/FALHOU em `#4ADE80`/`#F97066`; depois, com resultado de execução na tela, trocar para Light pelo menu ⋮ (itens System, Light e Dark) e confirmar que tudo volta ao claro sem recarregar e sem perder o resultado
