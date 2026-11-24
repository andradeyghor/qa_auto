# language: pt
Funcionalidade: Saque em Caixa Eletrônico (canônico)

  @CA-1 @CA-2 @CA-4 @caminho-1
  Cenário: Caminho 1: inserir_cartao → pin_valido → solicitar_saque → SaqueRecusado
    Dado que o sistema está no estado "Inicio"
    E que o contexto "saldo" vale 0.01
    Quando ocorre o evento "inserir_cartao"
    Então o sistema está no estado "AguardandoPin"
    Quando ocorre o evento "pin_valido"
    Então o sistema está no estado "Autenticado"
    # guarda: valor > saldo ou valor % 20 != 0
    Quando ocorre o evento "solicitar_saque" com:
      | valor | 0.01 |
    Então o sistema está no estado "SaqueRecusado"

  @CA-1 @CA-2 @CA-3 @CA-4 @caminho-2
  Cenário: Caminho 2: inserir_cartao → pin_invalido → pin_valido → solicitar_saque → SaqueRecusado
    Dado que o sistema está no estado "Inicio"
    E que o contexto "saldo" vale 0.01
    Quando ocorre o evento "inserir_cartao"
    Então o sistema está no estado "AguardandoPin"
    # guarda: tentativas < 2
    Quando ocorre o evento "pin_invalido"
    Então o sistema está no estado "AguardandoPin"
    Quando ocorre o evento "pin_valido"
    Então o sistema está no estado "Autenticado"
    # guarda: valor > saldo ou valor % 20 != 0
    Quando ocorre o evento "solicitar_saque" com:
      | valor | 0.01 |
    Então o sistema está no estado "SaqueRecusado"

  @CA-1 @CA-3 @caminho-3
  Cenário: Caminho 3: inserir_cartao → pin_invalido → pin_invalido → pin_invalido → CartaoRetido
    Dado que o sistema está no estado "Inicio"
    E que o contexto "saldo" vale 0.01
    Quando ocorre o evento "inserir_cartao"
    Então o sistema está no estado "AguardandoPin"
    # guarda: tentativas < 2
    Quando ocorre o evento "pin_invalido"
    Então o sistema está no estado "AguardandoPin"
    # guarda: tentativas < 2
    Quando ocorre o evento "pin_invalido"
    Então o sistema está no estado "AguardandoPin"
    # guarda: tentativas >= 2
    Quando ocorre o evento "pin_invalido"
    Então o sistema está no estado "CartaoRetido"

  @CA-1 @CA-2 @CA-4 @caminho-4
  Cenário: Caminho 4: inserir_cartao → pin_valido → solicitar_saque → SaqueRealizado
    Dado que o sistema está no estado "Inicio"
    E que o contexto "saldo" vale 20
    Quando ocorre o evento "inserir_cartao"
    Então o sistema está no estado "AguardandoPin"
    Quando ocorre o evento "pin_valido"
    Então o sistema está no estado "Autenticado"
    # guarda: valor <= saldo e valor % 20 == 0
    Quando ocorre o evento "solicitar_saque" com:
      | valor | 20 |
    Então o sistema está no estado "SaqueRealizado"

  @CA-1 @CA-2 @CA-4 @caminho-5 @borda
  Cenário: Caminho 5: inserir_cartao → pin_valido → solicitar_saque → SaqueRecusado
    Dado que o sistema está no estado "Inicio"
    E que o contexto "saldo" vale 20
    Quando ocorre o evento "inserir_cartao"
    Então o sistema está no estado "AguardandoPin"
    Quando ocorre o evento "pin_valido"
    Então o sistema está no estado "Autenticado"
    # guarda: valor > saldo ou valor % 20 != 0
    Quando ocorre o evento "solicitar_saque" com:
      | valor | 40 |
    Então o sistema está no estado "SaqueRecusado"
