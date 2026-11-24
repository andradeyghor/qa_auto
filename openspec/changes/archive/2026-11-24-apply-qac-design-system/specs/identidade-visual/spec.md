# Spec Delta

## Purpose

Garantir que a interface apresente a identidade QUALITY ASSURANCE CONSULTANT de forma consistente — nome, logo, tema, tipografia, hierarquia de ações e status de teste legíveis sem depender só da cor —, conforme o design kit do projeto.

## ADDED Requirements

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
A interface SHALL usar o favicon do kit como ícone da aba e SHALL exibir o logo horizontal claro no topo da barra lateral, trocando pelo ícone do app quando a barra lateral estiver recolhida. Os arquivos de logo e ícone SHALL ser os do kit, sem alteração de cor, orientação ou proporção.

#### Scenario: Logo na barra lateral
- **WHEN** o usuário abre o app com a barra lateral expandida
- **THEN** o logo horizontal (pato com chapéu e o nome) aparece no topo da barra lateral

#### Scenario: Ícone com a barra recolhida
- **WHEN** o usuário recolhe a barra lateral
- **THEN** o ícone do app (cabeça do pato em quadrado escuro) aparece no lugar do logo

#### Scenario: Favicon
- **WHEN** o app é aberto no navegador
- **THEN** a aba mostra o favicon do pato, e não um emoji

### Requirement: Paleta restrita aos tokens do kit
A interface SHALL usar apenas as cores definidas nos tokens do kit para o tema claro: fundo branco, superfícies cinza-claro, texto quase preto e amarelo de marca como única cor de destaque. O amarelo SHALL NOT ser usado como cor de texto sobre fundo claro. A interface SHALL NOT usar degradês nem as cores índigo/azul da identidade provisória.

#### Scenario: Tema claro aplicado
- **WHEN** o app é aberto
- **THEN** o fundo da página é #FFFFFF, a barra lateral e os cards usam #F4F4F4, o texto principal é #111111 e os controles nativos (abas ativas, checkbox, toggle, foco) usam #111111

#### Scenario: Sem cores da identidade anterior
- **WHEN** qualquer tela do app é renderizada
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
Cada etapa do fluxo SHALL ter no máximo uma ação primária, em fundo amarelo de marca com texto #111111: "Gerar testes" na etapa de entrada e "Executar testes" na etapa de execução. As demais ações, incluindo todos os downloads, SHALL ser secundárias: fundo transparente, borda #D4D4D4 e texto #111111.

#### Scenario: Ação primária da entrada
- **WHEN** o usuário vê o painel de entradas
- **THEN** o botão "Gerar testes" é o único botão primário do painel, em fundo amarelo com texto escuro

#### Scenario: Downloads secundários
- **WHEN** há artefatos gerados
- **THEN** o botão de baixar o pacote e os botões de baixar cada arquivo aparecem como botões secundários

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
O resultado de cada cenário executado SHALL ser exibido com a palavra "APROVADO" na cor de sucesso do kit (#15803D) ou "FALHOU" na cor de erro do kit (#B42318), sempre com a palavra presente, nunca só a cor. A cor de erro SHALL NOT aparecer como decoração fora de falhas e erros.

#### Scenario: Cenário aprovado
- **WHEN** um cenário passa na execução
- **THEN** a tabela de resultados mostra "APROVADO" para esse cenário

#### Scenario: Cenário com falha
- **WHEN** um cenário falha na execução
- **THEN** a tabela de resultados mostra "FALHOU" para esse cenário

#### Scenario: Veredito de bug detectado
- **WHEN** os testes passam no sistema correto e falham no sistema com bug
- **THEN** o veredito é exibido com texto explícito e a quantidade de testes que detectaram o bug, por exemplo "Bug detectado em 3 testes"

### Requirement: Diagrama de estados na paleta do kit
O diagrama de estados renderizado SHALL usar cores neutras do kit para nós, bordas e linhas, com o amarelo de marca apenas como destaque, e a fonte Inter.

#### Scenario: Cores do diagrama
- **WHEN** o usuário abre a aba do grafo
- **THEN** o diagrama não usa as cores índigo/azul anteriores e é desenhado sobre fundo branco ou #F4F4F4
