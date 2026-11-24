"""Gherkin em português, pacote executável e adaptadores (add-mbt-generator, tarefas 2.2 a 3.5 e 4.2)."""
import ast
import copy
import io
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

import exemplos
from backend.caminhos import ELEMENTARES, TRANSICOES, Caminho, Passo
from backend.compilador_gherkin import FRASES, ErroGherkin, gerar_feature, validar_feature
from backend.geracao import gerar_artefatos, normalizar_slug
from backend.gerador_pytest import MENSAGEM_ESQUELETO
from sistemas_exemplo import ErroSistema, obter

RAIZ = Path(__file__).resolve().parent.parent
SNAPSHOT = Path(__file__).resolve().parent / "snapshots" / "saque-atm.feature"
GABARITOS = ("saque-atm", "cupom-promocional", "mfa-bloqueio", "carrinho")
LIVRE = {
    "analise": "",
    "variaveis": [],
    "estados": [{"id": "A", "rotulo": "A", "tipo": "inicial"}, {"id": "B", "rotulo": "B", "tipo": "final"}],
    "transicoes": [{"id": "T1", "de": "A", "evento": "ir", "para": "B", "guarda": None, "acoes": [], "criterios": [1]}],
}
RECUSA = {
    "analise": "",
    "variaveis": [{"nome": "valor", "tipo": "decimal", "categoria": "entrada", "valor_inicial": None}],
    "estados": [{"id": "Inicio", "rotulo": "Início", "tipo": "inicial"}, {"id": "Fim", "rotulo": "Fim", "tipo": "final"}],
    "transicoes": [
        {"id": "T1", "de": "Inicio", "evento": "enviar", "para": "Fim", "guarda": "valor <= 10", "acoes": [],
         "criterios": [1]},
    ],
}


def gabarito(gabarito_id):
    return exemplos.carregar(gabarito_id)


def todos_os_modelos():
    return [(g, gabarito(g)["modelo"]) for g in GABARITOS] + [(s, obter(s).modelo) for s in ("login", "saque")]


def salvar(artefatos, pasta):
    for nome, conteudo in artefatos.arquivos().items():
        (pasta / nome).write_text(conteudo, encoding="utf-8")


def rodar(pasta, variante="correto", *extras):
    ambiente = {
        **os.environ, "PYTHONPATH": str(RAIZ), "QA_VARIANTE": variante, "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(pasta), "-q", "-p", "no:cacheprovider", f"--rootdir={pasta}", *extras],
        env=ambiente, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def cenarios(feature):
    return [l.strip() for l in feature.splitlines() if l.strip().startswith("Cenário:")]


# ---------------------------------------------------------------- 2.2 compilador: vocabulário, nomes e tags
def test_snapshot_do_saque_atm():
    g = gabarito("saque-atm")
    feature = gerar_artefatos(g["modelo"], slug="saque-atm", titulo=g["nome"]).feature
    assert feature == SNAPSHOT.read_text(encoding="utf-8")


def test_cabecalho_em_portugues():
    feature = gerar_artefatos(obter("login").modelo, "login").feature
    assert feature.startswith("# language: pt\nFuncionalidade: Login bancário\n")


def test_conteudo_do_cenario_com_contexto_e_dados():
    g = gabarito("saque-atm")
    feature = gerar_artefatos(g["modelo"], slug="saque-atm").feature
    bloco = feature.split("Cenário: Caminho 4:")[1].split("Cenário:")[0]
    assert 'Dado que o sistema está no estado "Inicio"' in bloco
    assert 'E que o contexto "saldo" vale 20' in bloco
    assert 'Quando ocorre o evento "solicitar_saque" com:\n      | valor | 20 |' in bloco
    assert 'Então o sistema está no estado "SaqueRealizado"' in bloco
    assert "# guarda: valor <= saldo e valor % 20 == 0" in bloco
    assert bloco.count("Quando ") == bloco.count("Então ") == 3


def test_passos_de_uma_transicao_com_guarda():
    """Cenário da spec: contexto saldo = 100 e evento solicitar_saque com valor = 80 até SaqueRealizado."""
    modelo = gabarito("saque-atm")["modelo"]
    caminho = Caminho("Inicio", (("saldo", 100),), (
        Passo("inserir_cartao", (), 0, "AguardandoPin"),
        Passo("pin_valido", (), 1, "Autenticado"),
        Passo("solicitar_saque", (("valor", 80),), 4, "SaqueRealizado"),
    ))
    feature = gerar_feature(modelo, [caminho], "Saque")
    assert 'E que o contexto "saldo" vale 100' in feature
    assert (
        'Quando ocorre o evento "solicitar_saque" com:\n      | valor | 80 |\n'
        '    Então o sistema está no estado "SaqueRealizado"'
    ) in feature


def test_nome_do_cenario_e_tags():
    feature = gerar_artefatos(gabarito("saque-atm")["modelo"], slug="saque-atm").feature
    assert "Cenário: Caminho 4: inserir_cartao → pin_valido → solicitar_saque → SaqueRealizado" in feature
    assert "  @CA-1 @CA-2 @CA-4 @caminho-4\n  Cenário: Caminho 4:" in feature
    assert "@caminho-5 @borda\n  Cenário: Caminho 5:" in feature
    assert len(set(cenarios(feature))) == len(cenarios(feature))


def test_caminho_sem_criterios_e_auxiliar():
    modelo = copy.deepcopy(LIVRE)
    modelo["transicoes"][0]["criterios"] = []
    feature = gerar_artefatos(modelo).feature
    assert "  @caminho-1 @auxiliar\n" in feature and "@CA-" not in feature


def test_evento_recusado_no_vocabulario():
    feature = gerar_artefatos(RECUSA).feature
    assert 'Então o evento é recusado e o sistema permanece no estado "Inicio"' in feature
    assert "| valor | 10.01 |" in feature


# ---------------------------------------------------------------- 2.3 todo .feature gerado passa no parser oficial
@pytest.mark.parametrize("bordas", [True, False])
@pytest.mark.parametrize("estrategia", [TRANSICOES, ELEMENTARES])
@pytest.mark.parametrize("nome, modelo", todos_os_modelos(), ids=[n for n, _ in todos_os_modelos()])
def test_feature_aceito_pelo_parser(nome, modelo, estrategia, bordas):
    artefatos = gerar_artefatos(modelo, estrategia=estrategia, bordas=bordas)
    documento = validar_feature(artefatos.feature)
    funcionalidade = documento["feature"]
    assert (funcionalidade["language"], funcionalidade["keyword"]) == ("pt", "Funcionalidade")
    assert len(funcionalidade["children"]) == len(artefatos.caminhos)
    for filho in funcionalidade["children"]:
        assert any(t["name"].startswith("@caminho-") for t in filho["scenario"]["tags"])


def test_parser_recusa_feature_quebrado():
    with pytest.raises(ErroGherkin):
        validar_feature("# language: pt\nFuncionalidade: x\n  Cenário: y\n    Dado a\n  Cenário sem dois pontos\n")


# ---------------------------------------------------------------- 2.4 texto do modelo tratado como dado
MALICIOSO = 'x"\n  Cenário: invadido\n    Dado import os; os.system("calc")'
PREFIXOS = ("# language: pt", "Funcionalidade:", "@", "Cenário:", "Dado ", "E ", "Quando ", "Então ", "|", "#")


def com_evento_malicioso():
    modelo = copy.deepcopy(LIVRE)
    modelo["transicoes"][0]["evento"] = MALICIOSO
    modelo["estados"][1]["rotulo"] = 'B" }'
    return modelo


def test_evento_malicioso_nao_altera_estrutura():
    feature = gerar_artefatos(com_evento_malicioso()).feature
    linhas = [l.strip() for l in feature.splitlines() if l.strip()]
    assert len(cenarios(feature)) == 1
    assert all(l.startswith(PREFIXOS) for l in linhas)
    validar_feature(feature)


def test_texto_do_modelo_nao_aparece_no_codigo():
    artefatos = gerar_artefatos(com_evento_malicioso())
    for codigo in (artefatos.script, artefatos.adaptador, artefatos.conftest):
        assert "calc" not in codigo and "invadido" not in codigo


# ---------------------------------------------------------------- 3.2 pacote com nomes consistentes
def test_nomes_consistentes():
    artefatos = gerar_artefatos(gabarito("saque-atm")["modelo"], slug="saque-atm")
    assert list(artefatos.arquivos()) == [
        "saque-atm.feature", "test_saque_atm.py", "adaptador_saque_atm.py", "conftest.py", "LEIAME.md",
        "saque-atm.json", "saque-atm.mmd", "cobertura.md",
    ]
    assert 'scenarios("saque-atm.feature")' in artefatos.script
    assert "from adaptador_saque_atm import Adaptador" in artefatos.conftest
    assert "python -m pytest" in artefatos.script
    for nome in ("saque-atm.feature", "test_saque_atm.py", "adaptador_saque_atm.py"):
        assert nome in artefatos.leiame


@pytest.mark.parametrize("sistema, slug, esperado", [
    ("login", None, "login"), (None, None, "requisito"), (None, "Cupom Promocional", "cupom-promocional"),
])
def test_slug(sistema, slug, esperado):
    assert gerar_artefatos(obter("login").modelo, sistema, slug=slug).slug == esperado


def test_normalizar_slug():
    assert normalizar_slug("Saque em Caixa Eletrônico") == "saque-em-caixa-eletronico"
    assert normalizar_slug("   ") == "requisito"


def test_sistema_desconhecido():
    with pytest.raises(ErroSistema, match="fantasma"):
        gerar_artefatos(LIVRE, "fantasma")


def test_seis_definicoes_de_passo():
    script = gerar_artefatos(LIVRE).script
    for frase in FRASES:
        assert f"parsers.parse({frase!r})" in script


# ---------------------------------------------------------------- 3.3 adaptador de simulação
@pytest.mark.parametrize("estrategia", [TRANSICOES, ELEMENTARES])
def test_gabaritos_passam_contra_a_simulacao(tmp_path, estrategia):
    for gabarito_id in GABARITOS:
        pasta = tmp_path / f"{gabarito_id}-{estrategia}"
        pasta.mkdir()
        artefatos = gerar_artefatos(gabarito(gabarito_id)["modelo"], slug=gabarito_id, estrategia=estrategia,
                                    adaptador="simulacao")
        salvar(artefatos, pasta)
        r = rodar(pasta, "correto", "-W", "error::pytest.PytestUnknownMarkWarning")
        assert r.returncode == 0, r.stdout
        assert f"{len(artefatos.caminhos)} passed" in r.stdout


# ---------------------------------------------------------------- 3.4 esqueleto
def test_esqueleto_falha_pedindo_o_adaptador(tmp_path):
    artefatos = gerar_artefatos(gabarito("cupom-promocional")["modelo"], slug="cupom-promocional")
    salvar(artefatos, tmp_path)
    r = rodar(tmp_path)
    assert r.returncode == 1, r.stdout
    assert f"{len(artefatos.caminhos)} failed" in r.stdout
    assert r.stdout.count(MENSAGEM_ESQUELETO) >= len(artefatos.caminhos)


# ---------------------------------------------------------------- 3.5 asserções reais
def definicoes_de_passo(script):
    for no in ast.walk(ast.parse(script)):
        if isinstance(no, ast.FunctionDef) and any(
            isinstance(d, ast.Call) and getattr(d.func, "id", "") in ("given", "when", "then") for d in no.decorator_list
        ):
            yield no


@pytest.mark.parametrize("sistema", ["login", None])
def test_codigo_sem_assercao_vazia(sistema):
    artefatos = gerar_artefatos(obter("login").modelo, sistema)
    passos = list(definicoes_de_passo(artefatos.script))
    assert len(passos) == 6
    for passo in passos:
        assert not all(isinstance(instrucao, ast.Pass) for instrucao in passo.body), passo.name
    for codigo in (artefatos.script, artefatos.adaptador, artefatos.conftest):
        assert "assert True" not in codigo
        assert not re.search(r"^\s+pass\s*$", codigo, flags=re.MULTILINE)


ADAPTADOR_QUE_ACEITA = '''class Adaptador:
    estado_atual = "Inicio"

    def definir_contexto(self, nome, valor):
        pass

    def disparar(self, evento, dados):
        return True
'''


def test_recusa_nao_confirmada(tmp_path):
    artefatos = gerar_artefatos(RECUSA, slug="recusa")
    salvar(artefatos, tmp_path)
    (tmp_path / artefatos.nome_adaptador).write_text(ADAPTADOR_QUE_ACEITA, encoding="utf-8")
    r = rodar(tmp_path)
    assert r.returncode == 1
    assert "O evento deveria ter sido recusado, mas foi aceito" in r.stdout


# ---------------------------------------------------------------- ponta a ponta com o sistema exemplo
@pytest.mark.parametrize("sistema_id", ["login", "saque"])
def test_referencia_passa_no_correto_e_falha_no_bug(sistema_id, tmp_path):
    salvar(gerar_artefatos(obter(sistema_id).modelo, sistema_id), tmp_path)
    correto = rodar(tmp_path, "correto")
    assert correto.returncode == 0, correto.stdout
    com_bug = rodar(tmp_path, "bug")
    assert com_bug.returncode == 1, com_bug.stdout
    assert "Esperado" in com_bug.stdout and "obtido" in com_bug.stdout


# ---------------------------------------------------------------- 4.2 pacote zip
def test_zip_descompactado_coleta_sem_erros(tmp_path):
    artefatos = gerar_artefatos(gabarito("saque-atm")["modelo"], slug="saque-atm", adaptador="simulacao")
    with zipfile.ZipFile(io.BytesIO(artefatos.zip())) as pacote:
        assert sorted(pacote.namelist()) == sorted(f"saque-atm/{n}" for n in artefatos.arquivos())
        pacote.extractall(tmp_path)
    r = rodar(tmp_path / "saque-atm", "correto", "--collect-only")
    assert r.returncode == 0, r.stdout
    assert f"{len(artefatos.caminhos)} tests collected" in r.stdout
