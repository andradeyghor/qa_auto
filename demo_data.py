"""Dados de demonstração do front (modo demo, sem backend/LLM)."""

EXEMPLOS = {
    "Login bancário": {
        "user_story": "Como um cliente bancário,\nQuero realizar o login no sistema,\nPara acessar minha conta corrente.",
        "criterios": "1. Senha correta redireciona para o Dashboard.\n2. Senha incorreta exibe mensagem de erro.\n3. Três tentativas erradas bloqueiam a conta.",
        "modelo": {
            "estados": ["Deslogado", "ValidandoCredenciais", "Dashboard", "ContaBloqueada"],
            "inicial": "Deslogado",
            "transicoes": [
                {"de": "Deslogado", "evento": "Submeter login", "para": "ValidandoCredenciais", "criterio": None},
                {"de": "ValidandoCredenciais", "evento": "Senha correta", "para": "Dashboard", "criterio": 1},
                {"de": "ValidandoCredenciais", "evento": "Senha incorreta", "para": "Deslogado", "criterio": 2},
                {"de": "ValidandoCredenciais", "evento": "Terceira falha", "para": "ContaBloqueada", "criterio": 3},
            ],
        },
        "gherkin": """Feature: Login do Cliente Bancário
  Como um cliente bancário
  Quero realizar o login no sistema
  Para acessar minha conta corrente

  Scenario: Login com sucesso (critério 1)
    Given que o usuário está no estado "Deslogado"
    When submeter as credenciais corretas
    Then o sistema transita para o estado "Dashboard"

  Scenario: Senha incorreta (critério 2)
    Given que o usuário está no estado "Deslogado"
    When submeter uma senha incorreta
    Then o sistema exibe mensagem de erro e retorna ao estado "Deslogado"

  Scenario: Conta bloqueada (critério 3)
    Given que o usuário errou a senha duas vezes
    When submeter uma senha incorreta pela terceira vez
    Then o sistema transita para o estado "ContaBloqueada"
""",
        "pytest": """import pytest
from pytest_bdd import scenarios, given, when, then

scenarios('login.feature')


@given('que o usuário está no estado "Deslogado"')
def estado_inicial():
    pass


@when('submeter as credenciais corretas')
def submeter_credenciais():
    pass


@then('o sistema transita para o estado "Dashboard"')
def validar_dashboard():
    assert True
""",
    },
    "Saque em caixa eletrônico": {
        "user_story": "Como um correntista,\nQuero sacar dinheiro no caixa eletrônico,\nPara ter dinheiro em espécie.",
        "criterios": "1. Saque com saldo suficiente entrega as notas e debita o valor.\n2. Saque com saldo insuficiente é recusado.\n3. Cartão é retido após três PINs incorretos.",
        "modelo": {
            "estados": ["AguardandoCartao", "ValidandoPIN", "MenuPrincipal", "CartaoRetido", "EntregandoNotas"],
            "inicial": "AguardandoCartao",
            "transicoes": [
                {"de": "AguardandoCartao", "evento": "Inserir cartão", "para": "ValidandoPIN", "criterio": None},
                {"de": "ValidandoPIN", "evento": "PIN correto", "para": "MenuPrincipal", "criterio": None},
                {"de": "ValidandoPIN", "evento": "Terceiro PIN errado", "para": "CartaoRetido", "criterio": 3},
                {"de": "MenuPrincipal", "evento": "Sacar com saldo", "para": "EntregandoNotas", "criterio": 1},
                {"de": "MenuPrincipal", "evento": "Sacar sem saldo", "para": "MenuPrincipal", "criterio": 2},
                {"de": "EntregandoNotas", "evento": "Retirar notas", "para": "AguardandoCartao", "criterio": None},
            ],
        },
        "gherkin": """Feature: Saque em caixa eletrônico
  Como um correntista
  Quero sacar dinheiro no caixa eletrônico
  Para ter dinheiro em espécie

  Scenario: Saque com saldo suficiente (critério 1)
    Given que o cliente está no estado "MenuPrincipal"
    When solicitar um saque dentro do saldo
    Then o sistema transita para o estado "EntregandoNotas"

  Scenario: Saque com saldo insuficiente (critério 2)
    Given que o cliente está no estado "MenuPrincipal"
    When solicitar um saque acima do saldo
    Then o sistema recusa o saque e permanece em "MenuPrincipal"

  Scenario: Cartão retido (critério 3)
    Given que o cliente errou o PIN duas vezes
    When informar um PIN incorreto pela terceira vez
    Then o sistema transita para o estado "CartaoRetido"
""",
        "pytest": """import pytest
from pytest_bdd import scenarios, given, when, then

scenarios('saque.feature')


@given('que o cliente está no estado "MenuPrincipal"')
def menu_principal():
    pass


@when('solicitar um saque dentro do saldo')
def saque_com_saldo():
    pass


@then('o sistema transita para o estado "EntregandoNotas"')
def validar_entrega():
    assert True
""",
    },
}
