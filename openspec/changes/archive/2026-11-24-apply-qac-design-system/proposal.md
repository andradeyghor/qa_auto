# Proposal

## Why

A interface Streamlit ainda usa a identidade provisória "QA Autonomous" (emoji 🤖, tema índigo com degradês azuis). O design kit em `assets/QUALITY ASSURANCE CONSULTANT/` define a identidade definitiva — nome, logo do pato, paleta neutra com amarelo de marca, tipografia Inter/JetBrains Mono e regras de iconografia — e pede que ela substitua a provisória no app. Sem isso, a entrega do front-end apresenta uma marca que já foi descontinuada.

## What Changes

- Renomear o app para **QUALITY ASSURANCE CONSULTANT** no `page_title`, no cabeçalho (hero) e no README; remover o nome "QA Autonomous" e o emoji 🤖 da interface.
- Copiar os arquivos dos grupos **Logos** e **Icones** do kit para `assets/` na raiz, com os mesmos nomes, e usá-los em `page_icon` (favicon) e `st.logo` (logo horizontal + ícone).
- Substituir o tema de `.streamlit/config.toml` pelo tema claro do kit (`primaryColor #111111`, `backgroundColor #FFFFFF`, `secondaryBackgroundColor #F4F4F4`, `textColor #111111`, borda `#D4D4D4`).
- Reescrever o CSS do `app.py` usando apenas os tokens do kit: sem degradês índigo/azul nem sombras coloridas; botão primário amarelo (`brand`) com texto `on-brand`; botões secundários e de download com borda `border`; cards em `surface`; código em JetBrains Mono; espaçamentos e raios da escala do kit.
- Hierarquia de ações: `type="primary"` só na ação principal de cada etapa ("Gerar testes" e "Executar testes"); os demais botões e downloads ficam secundários.
- Revisar rótulos para a voz do kit (curtos, no imperativo): por exemplo "Gerar testes", "Executar nas duas variantes", "Baixar cenários".
- Trocar os emojis da interface por ícones Material Symbols (`:material/...:`), eliminando os proibidos pelo kit (robô, lupa, inseto, cérebro, faíscas ✨).
- Resultados de teste: aprovado em `status-success` com a palavra "APROVADO", falha em `status-error` com "FALHOU", sempre com texto junto da cor; vermelho fora de qualquer decoração.
- Diagrama Mermaid com cores neutras e amarelo de marca no lugar da paleta índigo.

- Renomear a marca também nos textos do backend que chegam ao usuário: docstrings dos scripts Pytest e do adaptador, `LEIAME.md` do pacote, título da API FastAPI e descrição da CLI. O `LEIAME.md` e os scripts são exibidos na interface, então mantê-los com a marca antiga violaria a regra de "nenhuma tela com QA Autonomous". O único snapshot (`tests/snapshots/saque-atm.feature`) não contém o nome e não muda.

Fora de escopo: tema escuro (o kit o descreve como opcional; o app segue em tema claro).

## Capabilities

### New Capabilities
- `identidade-visual`: identidade visual da interface — nome da marca, logo e ícones, tema e tokens de cor/tipografia/espaçamento, hierarquia de botões, iconografia permitida e apresentação de status de teste (aprovado/falhou) sem depender só da cor.

### Modified Capabilities
<!-- Nenhuma: o comportamento funcional das telas (entrada, demonstração, execução, diagrama) não muda; só a apresentação. -->

## Impact

- `app.py`: `st.set_page_config`, novo `st.logo`, bloco `CSS`, hero, rótulos e ícones de botões/abas/alertas, `tabela_cenarios`, `render_execucao`, `render_mermaid`.
- `.streamlit/config.toml`: tema substituído.
- `assets/`: novos arquivos `qac-*.svg` e `qac-*.png` na raiz de `assets/` (o kit original permanece em `assets/QUALITY ASSURANCE CONSULTANT/`).
- `backend/gerador_pytest.py`, `backend/main.py`, `backend/cli.py`, `backend/__init__.py`: troca do nome da marca em textos.
- `README.md`: título e menções à marca.
- `tests/test_interface.py`: testes novos para nome/ícone/rótulos; testes existentes que localizam elementos por chave seguem válidos.
- Sem mudança de dependências: Streamlit 1.65 já suporta `st.logo`, `:material/...:` e `borderColor`/`linkColor` no tema.
