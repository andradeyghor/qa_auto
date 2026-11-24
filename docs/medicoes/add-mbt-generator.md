# Medição do fluxo completo: `add-mbt-generator` (tarefa 5.1)

Execução em 2026-11-22, de ponta a ponta: requisito → LLM → modelo → caminhos e testes → execução. A extração usou `backend.servico` diretamente, o mesmo caminho da linha de comando (`python -m backend.cli gerar --requisito`), sem a API HTTP. Os artefatos foram gerados com a estratégia padrão (todas as transições) e com cenários de borda.

Configuração: `OLLAMA_MODEL=llama3.1:8b` (aquecido antes da primeira rodada, em 85 s), prompt `extracao-v2`, temperatura 0, semente 42, `QA_TIMEOUT_LLM=180`, `QA_ORCAMENTO_GERACAO=360` e 3 tentativas. Login e Saque usam o catálogo do sistema exemplo. Cupom, MFA e Carrinho são extração livre e ainda não têm sistema exemplo (chegam no `add-test-execution`), então os testes deles rodaram contra a simulação do próprio modelo extraído, o que só confirma que o pacote executa.

## Resultado por exemplo

| Exemplo | Modelo válido? | Tentativas | Tempo | Cobertura (estados · transições · critérios) | Cenários | Execução |
|---|---|---|---|---|---|---|
| Login bancário (catálogo) | **Sim** | 2 (inválida 52 s, válida 34 s) | 86 s | 5/5 · 4/4 · 3/3 | 2 | **Bug detectado**: 2 de 2 no sistema correto; no sistema com bug, "Esperado ContaBloqueada, obtido DuasFalhas" |
| Saque em caixa eletrônico (catálogo) | Não | 3 | 163 s | — | — | — |
| Cupom Promocional (livre) | Não | 3 | 198 s | — | — | — |
| Autenticação MFA (livre) | **Sim** | 1 | 51 s | 3/3 · 4/4 · 4/4 | 4 (1 de borda) | Simulação: 4 de 4 passaram |
| Carrinho de Compras (livre) | **Sim** | 2 (inválida 42 s, válida 35 s) | 77 s | 0/3 · 0/4 · 0/4 | 0 | Nenhum caminho viável; o pytest-bdd para na coleta com `NoScenariosFound` |

As rodadas levaram de 51 s a 198 s, e o total foi de 667 s com o aquecimento. **3 de 5 exemplos geraram modelo válido**, o mesmo número da medição do `fsm-model-v2`. As falhas também se repetem:

- **Saque:** nas 3 tentativas o LLM marcou um estado com saída como final (`EntregandoNotas` duas vezes e `MenuPrincipal` uma vez, os dois com a saída T8), erro `final_com_saida`.
- **Cupom:** a última tentativa teve 7 erros, entre eles `guardas_sobrepostas` entre `cupom_valido e data_atual <= validade e não cupom_usado` e `cupom_expirado`.

### Os modelos válidos, vistos de perto

- **Login: 4 das 6 transições do modelo de referência.** Falta a senha correta depois de uma ou duas senhas erradas, mas o caminho das três senhas erradas está no modelo. Os 2 cenários passam no sistema correto e o do bloqueio falha no sistema com bug. Um modelo incompleto ainda detecta o defeito quando o caminho que o expõe está nele.
- **MFA: errado por um.** O laço `codigo_incorreto [tentativas < 3]` só bloqueia no quarto código errado, e o critério 4 pede o bloqueio no terceiro. O modelo também aceita o código sem passar pela senha, porque `senha_correta` é um laço no estado inicial. Os testes gerados reproduzem esse comportamento: o cenário 3 bloqueia só no quarto erro, e o cenário de borda afirma que, depois de três códigos errados, o código correto ainda libera o acesso. Contra a simulação do próprio modelo, tudo passa. Só um sistema alvo, ou a comparação com o gabarito, mostraria o erro.
- **Carrinho: válido, mas sem caminho até o final.** `adicionar_produto` não incrementa `itens_no_carrinho`, então a guarda `itens_no_carrinho > 0` de `finalizar_compra` nunca é verdadeira, e `Pagamento`, o único estado final, fica inalcançável. A validação aceitou o modelo porque confere a alcançabilidade sem considerar as guardas. O relatório de cobertura mostrou o problema:
  - T3: "nenhum valor candidato satisfaz a guarda";
  - T1, T2 e T4: "não há caminho viável até um estado final depois da transição";
  - borda de `itens_no_carrinho > 0`: omitida, com o motivo.

## Com o modelo de referência (demonstração)

Para comparar, os mesmos exemplos gerados do modelo de referência do sistema exemplo ou do gabarito, sem LLM:

| Exemplo | Transições cobertas | Cenários (de borda) | Execução |
|---|---|---|---|
| Login bancário | 6/6 | 4 (0) | Bug detectado |
| Saque em caixa eletrônico | 10/10 | 5 (0) | Bug detectado |
| Cupom Promocional | 4/4 | 7 (3) | Esqueleto; simulação: 7 de 7 |
| Autenticação MFA | 5/5 | 5 (1) | Esqueleto; simulação: 5 de 5 |
| Carrinho de Compras | 5/5 | 4 (0; 1 borda omitida) | Esqueleto; simulação: 4 de 4 |

No Carrinho, a borda omitida é a de `itens >= 1`: o valor de fora (`itens = 0`) não existe no estado `CarrinhoComItens`.

## O que a medição mostra

1. **O fluxo completo funciona nos dois modos.** Com catálogo e sistema exemplo (Login), o requisito virou modelo, testes e o veredito "Bug detectado", sem intervenção. Com extração livre (MFA), o pacote gerado executou e passou contra a simulação do modelo.
2. **A cobertura passou a ser um segundo filtro sobre o modelo.** O Carrinho passou na validação, mas o relatório mostrou 0% de cobertura e o motivo de cada transição. A validação confere a estrutura do grafo. O gerador confere se as guardas e as ações deixam chegar a um estado final.
3. **Testes gerados de um modelo errado passam contra o próprio modelo.** O MFA errado por um gerou testes coerentes com o erro, inclusive na borda. Por isso a execução contra um sistema alvo é o que mede se o modelo está certo. O `add-test-execution` amplia essa execução com mutantes e com os sistemas de Cupom, MFA e Carrinho.
4. **A extração continua sendo o elo mais fraco.** Saque e Cupom falharam pelas mesmas classes de erro das medições anteriores.

## Pontos para os próximos changes

- **Modelo sem caminho viável.** Hoje o `.feature` sai sem cenários e o pytest-bdd interrompe a coleta com `NoScenariosFound`. A interface poderia avisar antes, apontando para a aba Cobertura. A falta de caminho até um estado final também poderia voltar ao LLM como erro de validação, como já acontece com os erros estruturais.
- **Erros semânticos.** O erro por um do MFA só aparece contra um sistema alvo ou contra o gabarito. Isso reforça a avaliação por propriedades (`extraction-evaluation`) e os sistemas exemplo do `add-test-execution`.
- **Variância.** Os números são de uma única rodada por exemplo, com temperatura 0 e semente fixa.
