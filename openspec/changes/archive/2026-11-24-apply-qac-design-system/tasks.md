# Tasks

## 1. Arquivos da marca e tema

- [x] 1.1 Copiar `qac-logo-horizontal-claro.svg`, `qac-logo-horizontal-escuro.svg`, `qac-simbolo-claro.svg`, `qac-simbolo-escuro.svg` (de `assets/QUALITY ASSURANCE CONSULTANT/QUALITY ASSURANCE CONSULTANT/assets/Logos/`) e `qac-icone-escuro.svg`, `qac-icone-claro.svg`, `qac-icone-512.png`, `qac-favicon-32.png` (de `.../assets/Icones/`) para `assets/` na raiz; verificar com `ls assets/qac-*` que os 8 arquivos existem e são idênticos aos originais (`cmp`)
- [x] 1.2 Substituir `.streamlit/config.toml` pelo tema claro do kit (`primaryColor #111111`, `backgroundColor #FFFFFF`, `secondaryBackgroundColor #F4F4F4`, `textColor #111111`, `borderColor #D4D4D4`, `linkColor #111111`, `font "sans serif"`); verificar que `streamlit run app.py` sobe sem aviso de opção de tema inválida

## 2. Nome, logo e tokens

- [x] 2.1 Em `app.py`, definir `ASSETS = Path(__file__).parent / "assets"` e o dicionário `TOKENS` com as cores do tema claro de `tokens.json`; adicionar em `tests/test_interface.py` um teste que lê `tokens.json` do kit e compara com `TOKENS`, e verificar que passa
- [x] 2.2 Trocar `st.set_page_config` para `page_title="QUALITY ASSURANCE CONSULTANT"` e `page_icon` = favicon do kit, e adicionar `st.logo(logo horizontal claro, icon_image=ícone escuro)`; verificar com teste `AppTest` que o app roda sem exceção e que o `st.logo` recebe os caminhos de `ASSETS`
- [x] 2.3 Reescrever o hero: título "QUALITY ASSURANCE CONSULTANT" em estilo `display`, tagline "De requisitos a testes executáveis.", stepper com badges neutros; verificar com teste que o markdown do hero contém o nome e a tagline e que nenhum elemento renderizado contém "QA Autonomous" ou "🤖"

## 3. CSS e hierarquia de botões

- [x] 3.1 Substituir o bloco `CSS` inteiro por estilos gerados de `TOKENS`: fontes Inter/JetBrains Mono, botão primário `brand`/`on-brand` com hover `brand-strong`, botões secundários e `.stDownloadButton` com borda `border`, cards/métricas/sidebar/`.about` em `surface`, badges em estilo `label`, abas com destaque `accent-ink`, sem degradês, sombras coloridas ou animações; verificar com teste que o CSS não contém `#4f46e5`, `#4338ca`, `#0284c7`, `#6366f1` nem `gradient`
- [x] 3.2 Garantir `type="primary"` apenas em "Gerar testes" (`key="gerar"`) e "Executar testes" (`key="executar"`); demais botões e downloads secundários; verificar com teste que `at.button(key="gerar").proto.type == "primary"` e que os `download_button` não são primários
- [x] 3.3 Recolorir métricas e badges (DEMO em `brand`/`on-brand`, API REAL neutro, critérios completos em `status-success`, incompletos com badge "PARCIAL" sem âmbar) e o `render_mermaid` com a paleta neutra do kit; verificar com teste que o HTML do Mermaid não contém as cores índigo/azul antigas

## 4. Rótulos e ícones

- [x] 4.1 Revisar rótulos na voz do kit: "Gerar testes", "Executar testes", "Baixar pacote (…)", "Baixar <arquivo>", títulos de painel "Entradas" e "Artefatos gerados"; verificar com teste `AppTest` os rótulos de `key="gerar"`, `key="executar"` e `key="baixar_zip"`
- [x] 4.2 Trocar todos os emojis de rótulos, abas, expansores, alertas e textos pelos ícones Material Symbols do mapa em design.md, e o estado vazio pelo símbolo do pato; verificar com teste que, no estado inicial, após gerar (demo) e após executar, nenhum texto renderizado contém 🤖 🔍 🔎 🐛 🐞 🧠 ✨, e conferir visualmente que cada ícone renderiza (nenhum nome `:material/...:` aparece como texto cru)
- [x] 4.3 Trocar "QA Autonomous" por "QUALITY ASSURANCE CONSULTANT" nos textos de `backend/gerador_pytest.py` (script, adaptador de simulação, `LEIAME.md`), `backend/main.py` (título da API), `backend/cli.py` (descrição) e `backend/__init__.py`; verificar com `grep -rn "QA Autonomous" backend/` vazio e com o teste da 4.2 passando após gerar e executar

## 5. Status de teste

- [x] 5.1 Alterar `tabela_cenarios` para "APROVADO"/"FALHOU" com cor `status-success`/`status-error` via `pandas.Styler` na coluna Resultado, e `RESULTADO_TENTATIVA` para "VÁLIDO"/"INVÁLIDO"/"TIMEOUT"; verificar com teste que, após executar no exemplo de saque, a tabela do sistema correto só tem "APROVADO" e a do sistema com bug tem ao menos um "FALHOU"
- [x] 5.2 Exibir o veredito de bug detectado com a contagem ("Bug detectado em N teste(s)"); verificar com teste que a mensagem de sucesso contém o número de falhas da variante com bug

## 6. Documentação e verificação final

- [x] 6.1 Atualizar `README.md`: título "QUALITY ASSURANCE CONSULTANT", logo horizontal claro no topo, remoção de "QA Autonomous"/🤖 na parte do front-end; verificar com `grep` que o README não contém mais 🤖
- [x] 6.2 Rodar `pytest` completo e verificar que toda a suíte passa (inclusive snapshots, que não devem mudar)
- [x] 6.3 Abrir o app com `streamlit run app.py` e conferir visualmente, em modo demonstração, estado vazio, resultado gerado, todas as abas e a execução nas duas variantes: logo, favicon, botão amarelo único por etapa, tipografia e status APROVADO/FALHOU

## Workflow follow-up

- Arquivar a mudança após revisão.
