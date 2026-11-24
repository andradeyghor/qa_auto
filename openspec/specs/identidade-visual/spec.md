# identidade-visual Specification

## Purpose

Garantir que a interface apresente a identidade QUALITY ASSURANCE CONSULTANT de forma consistente — nome, logo, tema, tipografia, hierarquia de ações e status de teste legíveis sem depender só da cor —, conforme o design kit do projeto.

## Requirements

### Requirement: Nome da marca na interface
A interface SHALL exibir o nome QUALITY ASSURANCE CONSULTANT, sempre em caixa alta, como título da aba do navegador e como título do cabeçalho da página. A interface SHALL NOT exibir o nome provisório "QA Autonomous" nem o emoji de robô.

#### Scenario: Título da aba e cabeçalho
- **WHEN** o usuário abre o app
- **THEN** o título da aba do navegador é "QUALITY ASSURANCE CONSULTANT"
- **AND** o cabeçalho da página mostra "QUALITY ASSURANCE CONSULTANT" com a tagline "De requisitos a testes executáveis."

#### Scenario: Marca provisória ausente
- **WHEN** qualquer tela do app é renderizada, com ou sem resultado gerado
- **THEN** o texto "QA Autonomous" e o emoji 🤖 não aparecem

### Requirement: Logo e ícone do app
A interface SHALL usar o favicon do kit como ícone da aba e SHALL exibir o logo horizontal no topo da barra lateral, trocando pelo ícone do app quando a barra lateral estiver recolhida. No tema claro SHALL ser usada a versão clara do logo e, no tema escuro, a versão escura (chapéu claro). O mesmo vale para o símbolo do pato exibido no estado vazio. Os arquivos de logo e ícone SHALL ser os do kit, sem alteração de cor, orientação ou proporção.

#### Scenario: Logo na barra lateral
- **WHEN** o usuário abre o app com a barra lateral expandida
- **THEN** o logo horizontal (pato com chapéu e o nome) aparece no topo da barra lateral

#### Scenario: Logo no tema escuro
- **WHEN** o app está no tema escuro
- **THEN** o logo da barra lateral e o pato do estado vazio são as versões escuras do kit, com chapéu claro e nome em branco

#### Scenario: Ícone com a barra recolhida
- **WHEN** o usuário recolhe a barra lateral
- **THEN** o ícone do app (cabeça do pato em quadrado escuro) aparece no lugar do logo

#### Scenario: Favicon
- **WHEN** o app é aberto no navegador
- **THEN** a aba mostra o favicon do pato, e não um emoji

### Requirement: Paleta restrita aos tokens do kit
A interface SHALL usar apenas as cores definidas nos tokens do kit para o tema ativo, com o amarelo de marca como única cor de destaque. No tema claro, o amarelo SHALL NOT ser usado como cor de texto sobre fundo claro. A interface SHALL NOT usar degradês nem as cores índigo/azul da identidade provisória.

#### Scenario: Tema claro aplicado
- **WHEN** o app está no tema claro
- **THEN** o fundo da página é #FFFFFF, a barra lateral e os cards usam #F4F4F4, o texto principal é #111111 e os controles nativos (abas ativas, checkbox, toggle, foco) usam #111111

#### Scenario: Tema escuro aplicado
- **WHEN** o app está no tema escuro
- **THEN** o fundo da página é #111111, a barra lateral e os cards usam #2B2B2B, as bordas usam #4A4A4A, o texto principal é #FFFFFF e os controles nativos usam o amarelo de marca #FFC72C

#### Scenario: Sem cores da identidade anterior
- **WHEN** qualquer tela do app é renderizada, em qualquer tema
- **THEN** nenhum elemento usa as cores índigo/azul anteriores (#4f46e5, #4338ca, #0284c7, #6366f1) nem fundo em degradê

### Requirement: Tipografia do kit
A interface SHALL usar Inter para todo o texto e JetBrains Mono para os blocos de Gherkin, Pytest, Mermaid e JSON, com títulos de seção em peso 700 ou superior.

#### Scenario: Código em fonte monoespaçada
- **WHEN** o usuário abre a aba de Gherkin ou de Pytest
- **THEN** o código é exibido em JetBrains Mono (ou na fonte monoespaçada de reserva do kit)

#### Scenario: Texto da interface em Inter
- **WHEN** o app é renderizado
- **THEN** rótulos, títulos e texto corrido usam Inter (ou a fonte sem serifa de reserva do kit)

### Requirement: Hierarquia de ações
Cada etapa do fluxo SHALL ter no máximo uma ação primária, em fundo amarelo de marca com texto #111111, nos dois temas: "Gerar testes" na etapa de entrada e "Executar testes" na etapa de execução. As demais ações, incluindo todos os downloads, SHALL ser secundárias: fundo transparente, borda na cor `border` e texto na cor `text` do tema ativo.

#### Scenario: Ação primária da entrada
- **WHEN** o usuário vê o painel de entradas
- **THEN** o botão "Gerar testes" é o único botão primário do painel, em fundo amarelo com texto escuro

#### Scenario: Downloads secundários
- **WHEN** há artefatos gerados
- **THEN** o botão de baixar o pacote e os botões de baixar cada arquivo aparecem como botões secundários

#### Scenario: Botões no tema escuro
- **WHEN** o app está no tema escuro
- **THEN** o botão primário mantém fundo #FFC72C com texto #111111
- **AND** os botões secundários têm borda #4A4A4A e texto #FFFFFF

### Requirement: Rótulos na voz do kit
Os rótulos de ação SHALL ser curtos, no imperativo e em português do Brasil, mantendo em inglês os termos consagrados (User Story, Gherkin, Pytest, bug). Os vereditos e resumos SHALL ser frases verificáveis, com números quando houver.

#### Scenario: Rótulos dos botões
- **WHEN** o usuário vê a interface com artefatos gerados e um sistema alvo selecionado
- **THEN** os botões de ação usam rótulos como "Gerar testes", "Executar testes" e "Baixar pacote"

### Requirement: Iconografia permitida
Os ícones da interface (botões, abas, alertas, expansores e títulos de painel) SHALL ser ícones de traço simples do conjunto Material Symbols. A interface SHALL NOT exibir ícones ou emojis de robô, lupa, inseto, cérebro ou faíscas; o único personagem SHALL ser o pato do logo.

#### Scenario: Abas de resultado
- **WHEN** há artefatos gerados
- **THEN** as abas de resultado usam ícones Material Symbols, sem emojis

#### Scenario: Ícones proibidos
- **WHEN** qualquer tela do app é renderizada, inclusive estado vazio, importação de arquivo e alertas
- **THEN** os emojis 🤖, 🔍, 🔎, 🐛, 🐞, 🧠 e ✨ não aparecem

### Requirement: Status de teste com texto e cor
O resultado de cada cenário executado SHALL ser exibido com a palavra "APROVADO" na cor de sucesso do kit ou "FALHOU" na cor de erro do kit, na variante do tema ativo (claro: #15803D e #B42318; escuro: #4ADE80 e #F97066), sempre com a palavra presente, nunca só a cor. A cor de erro SHALL NOT aparecer como decoração fora de falhas e erros.

#### Scenario: Cenário aprovado
- **WHEN** um cenário passa na execução
- **THEN** a tabela de resultados mostra "APROVADO" para esse cenário

#### Scenario: Cenário com falha
- **WHEN** um cenário falha na execução
- **THEN** a tabela de resultados mostra "FALHOU" para esse cenário

#### Scenario: Status no tema escuro
- **WHEN** a execução é exibida no tema escuro
- **THEN** "APROVADO" aparece em #4ADE80 e "FALHOU" em #F97066

#### Scenario: Veredito de bug detectado
- **WHEN** os testes passam no sistema correto e falham no sistema com bug
- **THEN** o veredito é exibido com texto explícito e a quantidade de testes que detectaram o bug, por exemplo "Bug detectado em 3 testes"

### Requirement: Diagrama de estados na paleta do kit
O diagrama de estados renderizado SHALL usar cores neutras do kit do tema ativo para nós, bordas, linhas e texto, com o amarelo de marca apenas como destaque, e a fonte Inter.

#### Scenario: Cores do diagrama
- **WHEN** o usuário abre a aba do grafo no tema claro
- **THEN** o diagrama não usa as cores índigo/azul anteriores e é desenhado sobre fundo branco ou #F4F4F4

#### Scenario: Diagrama no tema escuro
- **WHEN** o usuário abre a aba do grafo no tema escuro
- **THEN** o diagrama é desenhado sobre fundo #111111 ou #2B2B2B, com texto e linhas claros

### Requirement: Temas claro e escuro do kit
O app SHALL oferecer o tema claro e o tema escuro do design kit. Ao abrir, SHALL seguir o tema do sistema operacional, e o usuário SHALL poder escolher Claro, Escuro ou Sistema no menu de configurações do app. A troca SHALL acontecer sem recarregar a página e sem descartar o resultado gerado na sessão.

#### Scenario: Sistema em modo escuro
- **WHEN** o usuário abre o app num sistema configurado em modo escuro
- **THEN** o app é exibido no tema escuro do kit

#### Scenario: Troca pelo menu
- **WHEN** o usuário, com artefatos gerados na tela, escolhe o tema Escuro no menu de configurações
- **THEN** a interface passa ao tema escuro
- **AND** o modelo, os artefatos e o resultado da execução continuam na tela

#### Scenario: Volta ao claro
- **WHEN** o usuário escolhe o tema Claro no menu de configurações
- **THEN** a interface volta ao tema claro do kit

### Requirement: Indicação de onde trocar o tema
A barra lateral SHALL exibir uma legenda curta informando que o tema claro ou escuro é escolhido no menu de configurações do app.

#### Scenario: Legenda na barra lateral
- **WHEN** o usuário abre o app com a barra lateral expandida
- **THEN** a barra lateral mostra uma legenda indicando o caminho do menu para trocar o tema
