import re

import pytest

from backend.schemas import ModeloEstados, criterios_cobertos, estado_inicial, estados_finais, ids_estados
from backend.validacao import validar_modelo
from sistemas_exemplo import SISTEMAS, ErroSistema, criar, obter


def percorrer(sistema, *eventos):
    for evento in eventos:
        sistema.disparar(evento)
    return sistema.estado


# catálogo e criação
def test_sistemas_disponiveis():
    assert set(SISTEMAS) == {"login", "saque"}
    assert all(d.nome for d in SISTEMAS.values())


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_catalogo_completo(sistema_id):
    catalogo = obter(sistema_id).catalogo
    assert catalogo.inicial in catalogo.estados
    assert all(catalogo.estados.values()) and all(catalogo.eventos.values())


@pytest.mark.parametrize("sistema_id", SISTEMAS)
@pytest.mark.parametrize("variante", ["correto", "bug"])
def test_cria_instancia_nova_no_inicial(sistema_id, variante):
    primeiro = criar(sistema_id, variante)
    assert primeiro.estado == obter(sistema_id).catalogo.inicial
    assert criar(sistema_id, variante) is not primeiro


def test_sistema_desconhecido():
    with pytest.raises(ErroSistema, match="fantasma"):
        criar("fantasma")


def test_variante_desconhecida():
    with pytest.raises(ErroSistema, match="outra"):
        criar("login", "outra")


def test_evento_fora_do_catalogo():
    with pytest.raises(ErroSistema, match="teletransportar"):
        criar("login").disparar("teletransportar")


def test_evento_nao_aplicavel_mantem_estado():
    sistema = criar("saque")
    assert percorrer(sistema, "retirar_notas") == "AguardandoCartao"


# interface do adaptador: contexto, dados no evento e aceitação (add-mbt-generator 3.1)
def test_evento_aplicavel_e_aceito():
    sistema = criar("login")
    assert sistema.disparar("senha_incorreta") is True
    assert sistema.estado_atual == "UmaFalha"
    assert criar("saque").disparar("inserir_cartao", {}) is True


def test_evento_nao_aplicavel_e_recusado_sem_erro():
    sistema = criar("saque")
    assert sistema.disparar("retirar_notas", {}) is False
    assert sistema.estado_atual == "AguardandoCartao"
    bloqueado = criar("login")
    percorrer(bloqueado, *["senha_incorreta"] * 3)
    assert bloqueado.disparar("senha_correta") is False
    assert bloqueado.estado_atual == "ContaBloqueada"


def test_saque_sem_saldo_e_recusado():
    sistema = criar("saque")
    percorrer(sistema, "inserir_cartao", "pin_correto")
    assert sistema.disparar("sacar_sem_saldo") is False
    assert sistema.estado_atual == "MenuPrincipal"


def test_laco_aceito_nao_muda_o_estado():
    """O retorno diz se a regra aceitou o evento, e não se o estado mudou."""
    sistema = criar("login", "bug")
    percorrer(sistema, "senha_incorreta", "senha_incorreta")
    assert sistema.disparar("senha_incorreta") is True
    assert sistema.estado_atual == "DuasFalhas"


def test_evento_fora_do_catalogo_com_dados():
    with pytest.raises(ErroSistema, match="teletransportar"):
        criar("saque").disparar("teletransportar", {"valor": 1})


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_contexto_desconhecido(sistema_id):
    with pytest.raises(ErroSistema, match="saldo"):
        criar(sistema_id).definir_contexto("saldo", 100)


@pytest.mark.parametrize("sistema_id", SISTEMAS)
@pytest.mark.parametrize("variante", ["correto", "bug"])
def test_estado_atual(sistema_id, variante):
    sistema = criar(sistema_id, variante)
    assert sistema.estado_atual == sistema.estado == obter(sistema_id).catalogo.inicial


# login
def test_login_tres_erros_bloqueiam_so_na_variante_correta():
    erros = ["senha_incorreta"] * 3
    assert percorrer(criar("login", "correto"), *erros) == "ContaBloqueada"
    assert percorrer(criar("login", "bug"), *erros) == "DuasFalhas"


def test_login_bloqueado_ignora_senha_correta():
    assert percorrer(criar("login"), *["senha_incorreta"] * 3, "senha_correta") == "ContaBloqueada"


# saque
SEM_SALDO = ["inserir_cartao", "pin_correto", "sacar_sem_saldo"]


def test_saque_sem_saldo_entrega_notas_so_na_variante_com_bug():
    assert percorrer(criar("saque", "correto"), *SEM_SALDO) == "MenuPrincipal"
    assert percorrer(criar("saque", "bug"), *SEM_SALDO) == "EntregandoNotas"


def test_saque_com_saldo_debita():
    sistema = criar("saque")
    saldo = sistema.saldo
    assert percorrer(sistema, "inserir_cartao", "pin_correto", "sacar_com_saldo") == "EntregandoNotas"
    assert sistema.saldo < saldo


def test_saque_tres_pins_retem_cartao():
    assert percorrer(criar("saque"), "inserir_cartao", *["pin_incorreto"] * 3) == "CartaoRetido"


# modelo de referência
@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_referencia_usa_somente_o_catalogo(sistema_id):
    definicao = obter(sistema_id)
    catalogo, modelo = definicao.catalogo, definicao.modelo
    assert estado_inicial(modelo) == catalogo.inicial
    assert set(ids_estados(modelo)) <= set(catalogo.estados)
    assert {v["nome"] for v in modelo["variaveis"]} <= set(catalogo.variaveis)
    for t in modelo["transicoes"]:
        assert {t["de"], t["para"]} <= set(catalogo.estados)
        assert t["evento"] in catalogo.eventos


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_catalogo_em_snake_case_e_pascal_case(sistema_id):
    catalogo = obter(sistema_id).catalogo
    assert all(re.fullmatch(r"[a-z][a-z0-9_]*", e) for e in catalogo.eventos)
    assert all(re.fullmatch(r"[A-Z][A-Za-z0-9]*", e) for e in catalogo.estados)


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_catalogo_sem_variaveis_conta_por_estados(sistema_id):
    assert obter(sistema_id).catalogo.variaveis == {}


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_referencia_cobre_todos_os_criterios(sistema_id):
    definicao = obter(sistema_id)
    numeros = {int(n) for n in re.findall(r"^(\d+)\.", definicao.criterios, flags=re.MULTILINE)}
    assert numeros and numeros == criterios_cobertos(definicao.modelo)


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_referencia_valida(sistema_id):
    definicao = obter(sistema_id)
    modelo = ModeloEstados.model_validate(definicao.modelo)
    assert validar_modelo(modelo, definicao.criterios, definicao.catalogo) == []


def test_final_do_login_sem_laco():
    modelo = obter("login").modelo
    assert not [t for t in modelo["transicoes"] if t["de"] in estados_finais(modelo)]


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_referencia_descreve_a_variante_correta(sistema_id):
    """Cada transição, reproduzida por um caminho até a origem, leva ao destino declarado."""
    definicao = obter(sistema_id)
    transicoes = definicao.modelo["transicoes"]
    caminhos = {definicao.catalogo.inicial: []}
    while True:
        novos = {
            t["para"]: caminhos[t["de"]] + [t["evento"]]
            for t in transicoes
            if t["de"] in caminhos and t["para"] not in caminhos
        }
        if not novos:
            break
        caminhos.update(novos)
    for t in transicoes:
        sistema = criar(sistema_id)
        assert percorrer(sistema, *caminhos[t["de"]], t["evento"]) == t["para"]


def test_comportamento_independe_do_modelo(monkeypatch):
    modelo = obter("login").modelo
    monkeypatch.setitem(modelo, "transicoes", [])
    assert percorrer(criar("login"), *["senha_incorreta"] * 3) == "ContaBloqueada"
