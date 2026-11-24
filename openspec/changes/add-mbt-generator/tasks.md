# Tasks

## 1. Caminhos de teste

- [x] 1.1 Implementar candidatos de valores e busca por configurações, com as camadas e o valor de contexto declarado da decisão 2; testes: o caminho para `CartaoRetido` no gabarito `saque-atm` tem 3 `pin_invalido`; o caminho até `SaqueRealizado` usa saldo 20 e valor 20, ou saldo 100 e valor 20 com o saldo declarado; uma guarda `valor <= 0` é coberta com valor 0
- [x] 1.2 Implementar a estratégia "todas as transições" com término em estado final; teste: 100% das transições cobertas nos gabaritos de Saque ATM, Cupom e MFA e nos modelos de referência de Login e Saque
- [x] 1.3 Implementar a estratégia "caminhos elementares" com limite; teste do aviso de limite atingido
- [x] 1.4 Implementar os cenários de borda, com fronteira entre variáveis, busca do valor de fora com limite de passos e evento recusado quando aplicável; testes: saldo declarado 100 com valores 100 e 120, e borda sem valor de fora válido informada no relatório de cobertura
- [x] 1.5 Implementar o relatório de cobertura com motivos; teste com transição além da profundidade máxima
- [x] 1.6 Teste de determinismo: duas execuções produzem a mesma saída byte a byte

## 2. Gherkin

- [x] 2.1 Adicionar `gherkin-official` e confirmar que ele e o `pytest-bdd` aceitam um `.feature` mínimo com `# language: pt`; registrar o resultado no design se houver desvio
- [x] 2.2 Implementar o compilador com vocabulário fixo, nomes de cenário e tags; teste com snapshot do `.feature` do Saque ATM
- [x] 2.3 Validar com o parser todo `.feature` gerado dos gabaritos e modelos de referência; teste parametrizado
- [x] 2.4 Manter o texto do modelo apenas como dado; o teste existente de evento malicioso passa com o vocabulário novo

## 3. Pytest e sistemas exemplo

- [x] 3.1 Estender `SistemaExemplo` com `definir_contexto`, `disparar(evento, dados) -> bool` e `estado_atual`; testes dos cenários da spec de `sistemas-exemplo`
- [x] 3.2 Gerar `test_<slug>.py`, adaptador, `conftest.py` e `LEIAME.md`; teste de nomes consistentes
- [x] 3.3 Implementar o adaptador de simulação do modelo; os testes gerados de todos os gabaritos passam contra ele
- [x] 3.4 Teste: com o adaptador de esqueleto, todos os cenários falham com "Implemente o adaptador do sistema sob teste"
- [x] 3.5 Teste estático: o código gerado não contém `assert True` nem passos com corpo `pass`; teste de recusa não confirmada
- [x] 3.6 Adaptar `backend/execucao.py` ao pacote novo; o teste de ponta a ponta do veredito continua dando "Bug detectado" para Login e Saque

## 4. Exportação e interface

- [x] 4.1 Abas Gherkin, Pytest e Cobertura com conteúdo gerado e downloads individuais; teste com `AppTest` nos modos real e demonstração
- [x] 4.2 Gerar o zip; teste descompacta e roda `pytest --collect-only` sem erros
- [x] 4.3 Implementar `python -m backend.cli gerar` com `--modelo` e `--requisito`; teste gera os artefatos do Saque ATM a partir do JSON e, com provedor fake, a partir do requisito
- [x] 4.4 Opções de estratégia e de borda na interface e na linha de comando; teste sem `@borda`
- [x] 4.5 Documentar a linha de comando e o pacote no README; conferir que o comando documentado funciona

## 5. Integração

- [x] 5.1 Rodar o fluxo completo (requisito → LLM → modelo → testes → execução) para os 5 exemplos e registrar cobertura e resultado em `docs/medicoes/add-mbt-generator.md`

## Workflow follow-up

- Arquivar antes de `add-test-execution`.
