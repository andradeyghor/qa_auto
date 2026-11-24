# Spec Delta

## MODIFIED Requirements

### Requirement: Cobertura de todas as transições
Na estratégia padrão, a geração MUST produzir caminhos viáveis, do estado inicial até um estado final, que em conjunto percorram todas as transições alcançáveis do modelo, preferindo caminhos mais curtos. Um caminho é viável quando cada guarda é verdadeira, com os valores escolhidos, no momento da transição.

#### Scenario: Todas cobertas
- **WHEN** caminhos são gerados do gabarito do Cupom
- **THEN** cada transição aparece em ao menos um caminho

#### Scenario: Início do caminho
- **WHEN** um caminho é gerado
- **THEN** ele começa no estado inicial, cada passo parte do estado em que o anterior terminou e o último estado é final

#### Scenario: Caminho com contador
- **WHEN** a transição para `CartaoRetido` exige `tentativas >= 2`
- **THEN** o caminho que a cobre tem três eventos `pin_invalido`

### Requirement: Cenários Gherkin verificam cada passo
Cada caminho MUST virar um cenário que define o estado inicial e os valores de contexto em `Dado`/`E`, dispara cada evento com seus dados em `Quando` e confere o estado resultante em `Então`, usando apenas as frases do vocabulário fixo.

#### Scenario: Conteúdo do cenário
- **WHEN** um caminho com dois eventos vira cenário
- **THEN** o cenário contém o estado inicial, dois `Quando` e dois `Então`

#### Scenario: Passos de uma transição com guarda
- **WHEN** o caminho parte de `Autenticado` com contexto `saldo = 100` e o evento `solicitar_saque` com `valor = 80` leva a `SaqueRealizado`
- **THEN** o cenário contém `E que o contexto "saldo" vale 100`, `Quando ocorre o evento "solicitar_saque" com:` seguido da tabela `| valor | 80 |` e `Então o sistema está no estado "SaqueRealizado"`

### Requirement: Rastreabilidade nos cenários
O nome de cada cenário MUST ser único e informar o número do caminho, a sequência de eventos e o estado final. Cada cenário MUST ter as tags `@CA-<n>` dos critérios percorridos, `@caminho-<n>` e, se for de borda, `@borda`.

#### Scenario: Nome do cenário
- **WHEN** o caminho 2 tem os eventos `inserir_cartao`, `pin_valido` e `solicitar_saque` e termina em `SaqueRealizado`
- **THEN** o cenário se chama "Caminho 2: inserir_cartao → pin_valido → solicitar_saque → SaqueRealizado"

#### Scenario: Caminho com critérios
- **WHEN** o caminho 3 cobre os critérios 2 e 4 e é de borda
- **THEN** o cenário tem as tags `@CA-2 @CA-4 @caminho-3 @borda`

#### Scenario: Caminho sem critérios
- **WHEN** um caminho percorre apenas transições sem critério
- **THEN** o cenário não tem tag `@CA-<n>` e tem a tag `@auxiliar`

### Requirement: Artefatos executáveis com sistema alvo
Com sistema alvo, a geração MUST produzir `<slug>.feature`, `test_<slug>.py`, um adaptador ligado ao sistema exemplo e um `conftest.py`, com nomes coerentes, cujos cenários têm todos os passos definidos e rodam contra o sistema.

#### Scenario: Par baixado executa
- **WHEN** os arquivos do pacote são salvos juntos com os nomes sugeridos e o comando indicado no teste é executado na raiz do projeto
- **THEN** todos os cenários são coletados e executados, sem erro de arquivo ou de passo ausente

#### Scenario: Variante selecionável
- **WHEN** o teste roda com a variante correta ou com bug selecionada por configuração de ambiente
- **THEN** os cenários executam contra a variante selecionada

#### Scenario: Divergência explicada
- **WHEN** o estado do sistema difere do esperado em um passo
- **THEN** o teste falha informando o estado esperado e o obtido

### Requirement: Esqueleto sem sistema alvo
Sem sistema alvo, a geração MUST produzir os mesmos arquivos com um adaptador cujas três operações falham com a mensagem "Implemente o adaptador do sistema sob teste".

#### Scenario: Esqueleto não passa sozinho
- **WHEN** o esqueleto é executado sem alterar o adaptador
- **THEN** os cenários são coletados e cada um falha com a mensagem "Implemente o adaptador do sistema sob teste"

## ADDED Requirements

### Requirement: Estratégia de caminhos elementares
Na estratégia de caminhos elementares, a geração MUST listar por busca em profundidade os caminhos viáveis que não repetem a mesma combinação de estado e valores das variáveis de estado, até o limite configurado de caminhos.

#### Scenario: Limite atingido
- **WHEN** existem mais caminhos que o limite de 200
- **THEN** são devolvidos 200 caminhos e o relatório avisa que o limite foi atingido

### Requirement: Escolha de valores do caminho
Para variáveis numéricas de contexto e de entrada, a geração MUST tentar primeiro combinações só com valores positivos, depois com zero e por último com negativos, passando à camada seguinte apenas quando a transição não é viável na anterior. Um valor declarado para uma variável de contexto MUST ser tentado antes dos demais candidatos.

#### Scenario: Valores positivos no caminho normal
- **WHEN** caminhos são gerados do gabarito `saque-atm`, sem valor declarado para `saldo`
- **THEN** o caminho até `SaqueRealizado` usa saldo 20 e valor 20

#### Scenario: Valor de contexto declarado
- **WHEN** a variável de contexto `saldo` do gabarito `saque-atm` declara o valor 100
- **THEN** o caminho até `SaqueRealizado` usa saldo 100 e valor 20

#### Scenario: Zero quando necessário
- **WHEN** uma transição tem a guarda `valor <= 0`
- **THEN** o caminho que a cobre usa valor 0

### Requirement: Cenários de borda
Para cada guarda que compara uma variável com um valor ou com outra variável, a geração MUST produzir, quando ativada, um cenário com o valor na fronteira e outro com o primeiro valor fora dela em que as demais condições da guarda mantêm o resultado que tinham na fronteira.

#### Scenario: Borda do saldo
- **WHEN** a variável de contexto `saldo` declara o valor 100 e a guarda é `valor <= saldo e valor % 20 == 0`
- **THEN** há um cenário com valor 100 e outro com valor 120

#### Scenario: Evento recusado na borda
- **WHEN** o valor fora da fronteira não satisfaz nenhuma transição do evento
- **THEN** o cenário termina com `Então o evento é recusado e o sistema permanece no estado "<estado>"`

#### Scenario: Borda sem valor de fora válido
- **WHEN** nenhum valor fora da fronteira, dentro do limite de passos, mantém o resultado das demais condições da guarda
- **THEN** o cenário de borda não é gerado e o relatório de cobertura informa o motivo

### Requirement: Relatório de cobertura
A geração MUST informar a porcentagem de estados, transições e critérios de aceite cobertos e listar cada elemento não coberto com o motivo.

#### Scenario: Transição além da profundidade máxima
- **WHEN** uma transição não é alcançada em até 30 passos
- **THEN** ela aparece como não coberta com o motivo "profundidade máxima atingida"

#### Scenario: Cobertura total
- **WHEN** todas as transições do modelo são cobertas
- **THEN** o relatório mostra 100% de transições e de critérios

### Requirement: Rastreabilidade do caminho
Cada caminho MUST informar a sequência de transições, os valores de contexto e de entrada usados e os critérios de aceite das transições percorridas.

#### Scenario: Critérios do caminho
- **WHEN** um caminho passa por transições dos critérios 1 e 3
- **THEN** o caminho informa os critérios 1 e 3 e os valores usados em cada evento

### Requirement: Arquivo .feature válido em português
O `.feature` gerado MUST começar com `# language: pt`, ter uma `Funcionalidade` com o título do exemplo e ser aceito pelo parser Gherkin oficial sem erros.

#### Scenario: Feature do Saque
- **WHEN** o Gherkin do Saque é gerado
- **THEN** o arquivo começa com `# language: pt` e uma `Funcionalidade:`
- **AND** o parser Gherkin o aceita sem erros

### Requirement: Definição para todo passo
Todo passo do `.feature` gerado MUST corresponder a exatamente uma definição de passo do teste gerado.

#### Scenario: Execução contra simulação do modelo
- **WHEN** os testes rodam com um adaptador que simula o próprio modelo
- **THEN** todos os cenários passam e nenhum passo fica sem definição

### Requirement: Asserções reais
Os passos `Então` MUST comparar o estado informado pelo adaptador com o esperado, e o passo de evento recusado MUST verificar a recusa e a permanência no estado. O teste gerado MUST NOT conter asserção sempre verdadeira nem passo vazio.

#### Scenario: Teste sem asserção vazia
- **WHEN** o arquivo de teste gerado é inspecionado
- **THEN** ele não contém `assert True` nem definição de passo com corpo `pass`

#### Scenario: Recusa não confirmada
- **WHEN** o cenário espera recusa e o adaptador informa que o evento foi aceito
- **THEN** o teste falha informando que o evento deveria ter sido recusado
