"""Linha de comando de geração (add-mbt-generator, tarefas 4.3 a 4.5)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import backend.servico
import exemplos
from backend import cli, provedores
from backend.provedores.base import Provedor
from sistemas_exemplo import obter

RAIZ = Path(__file__).resolve().parent.parent
GABARITO = RAIZ / "exemplos" / "saque-atm.json"
PACOTE = ("saque-atm.json", "saque-atm.mmd", "saque-atm.feature", "test_saque_atm.py", "adaptador_saque_atm.py",
          "conftest.py")


def ambiente():
    return {**os.environ, "PYTHONPATH": str(RAIZ), "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}


def pytest_no_pacote(pasta, *extras):
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(pasta), "-q", "-p", "no:cacheprovider", f"--rootdir={pasta}", *extras],
        env=ambiente(), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


@pytest.fixture
def sem_llm(monkeypatch):
    def falha(*a, **k):
        raise AssertionError("o LLM não deveria ser chamado")

    monkeypatch.setattr(backend.servico, "gerar", falha)


class ProvedorFalso(Provedor):
    id = "falso"
    nome = "Falso"
    modelo_fixo = "falso-1"

    def chamar(self, system, mensagens, *, modelo=None, timeout=None, api_key=None):
        return json.dumps(exemplos.carregar("saque-atm")["modelo"])


@pytest.fixture
def provedor_falso(monkeypatch):
    monkeypatch.setitem(provedores.REGISTRO, "falso", ProvedorFalso())


# ---------------------------------------------------------------- 4.3 a partir do modelo e do requisito
def test_cenario_minimo_a_partir_do_modelo(tmp_path, sem_llm, capsys):
    saida = tmp_path / "saida"
    assert cli.main(["gerar", "--modelo", str(GABARITO), "--saida", str(saida)]) == 0
    assert all((saida / nome).is_file() for nome in PACOTE)
    assert (saida / "saque-atm.feature").read_text(encoding="utf-8").startswith(
        "# language: pt\nFuncionalidade: Saque em Caixa Eletrônico (canônico)\n"
    )
    assert json.loads((saida / "saque-atm.json").read_text(encoding="utf-8")) == exemplos.carregar("saque-atm")["modelo"]
    assert "Cobertura: estados 6/6 (100%)" in capsys.readouterr().out
    coleta = pytest_no_pacote(saida, "--collect-only")
    assert coleta.returncode == 0, coleta.stdout


def test_a_partir_do_requisito_com_provedor_falso(tmp_path, provedor_falso, capsys):
    g = exemplos.carregar("saque-atm")
    requisito = tmp_path / "requisito.md"
    requisito.write_text(f"# História\n{g['historia']}\n\n# Critérios\n{g['criterios']}\n", encoding="utf-8")
    saida = tmp_path / "saida"
    assert cli.main(["gerar", "--requisito", str(requisito), "--motor", "falso", "--saida", str(saida)]) == 0
    assert all((saida / n).is_file() for n in ("requisito.json", "requisito.mmd", "requisito.feature",
                                                 "test_requisito.py", "adaptador_requisito.py", "conftest.py"))
    assert "Modelo extraído por falso (falso-1) em 1 tentativa(s)" in capsys.readouterr().out


def test_com_sistema_alvo_o_pacote_executa(tmp_path, sem_llm):
    modelo = tmp_path / "login.json"
    modelo.write_text(json.dumps(obter("login").modelo), encoding="utf-8")
    saida = tmp_path / "saida"
    assert cli.main(["gerar", "--modelo", str(modelo), "--sistema", "login", "--saida", str(saida)]) == 0
    r = pytest_no_pacote(saida)
    assert r.returncode == 0, r.stdout


# ---------------------------------------------------------------- 4.4 estratégia e bordas
def test_sem_borda(tmp_path, sem_llm):
    saida = tmp_path / "saida"
    assert cli.main(["gerar", "--modelo", str(GABARITO), "--sem-borda", "--saida", str(saida)]) == 0
    assert "@borda" not in (saida / "saque-atm.feature").read_text(encoding="utf-8")


def test_estrategia_elementares(tmp_path, sem_llm):
    carrinho = RAIZ / "exemplos" / "carrinho.json"
    contagem = {}
    for estrategia in ("transicoes", "elementares"):
        saida = tmp_path / estrategia
        assert cli.main(["gerar", "--modelo", str(carrinho), "--estrategia", estrategia, "--saida", str(saida)]) == 0
        contagem[estrategia] = (saida / "carrinho.feature").read_text(encoding="utf-8").count("Cenário:")
    assert contagem["elementares"] > contagem["transicoes"]


# ---------------------------------------------------------------- erros
def test_modelo_invalido(tmp_path, sem_llm, capsys):
    modelo = json.loads(GABARITO.read_text(encoding="utf-8"))["modelo"]
    modelo["transicoes"] = [t for t in modelo["transicoes"] if t["id"] != "T4"]
    arquivo = tmp_path / "quebrado.json"
    arquivo.write_text(json.dumps(modelo), encoding="utf-8")
    assert cli.main(["gerar", "--modelo", str(arquivo), "--saida", str(tmp_path / "saida")]) == 1
    assert "tem erros" in capsys.readouterr().err
    assert not (tmp_path / "saida").exists()


def test_arquivo_que_nao_e_json(tmp_path, sem_llm, capsys):
    arquivo = tmp_path / "x.json"
    arquivo.write_text("não é json", encoding="utf-8")
    assert cli.main(["gerar", "--modelo", str(arquivo), "--saida", str(tmp_path / "saida")]) == 1
    assert "Não foi possível ler o modelo" in capsys.readouterr().err


def test_requisito_exige_motor(tmp_path):
    with pytest.raises(SystemExit) as saida:
        cli.main(["gerar", "--requisito", "r.md", "--saida", str(tmp_path)])
    assert saida.value.code == 2


def test_requisito_sem_historia(tmp_path, provedor_falso, capsys):
    requisito = tmp_path / "r.md"
    requisito.write_text("# Critérios\n1. a\n", encoding="utf-8")
    assert cli.main(["gerar", "--requisito", str(requisito), "--motor", "falso", "--saida", str(tmp_path / "s")]) == 1
    assert "história de usuário não foi encontrada" in capsys.readouterr().err


# ---------------------------------------------------------------- 4.5 o comando documentado funciona
def test_comando_documentado_no_readme(tmp_path):
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert "python -m backend.cli gerar --modelo exemplos/saque-atm.json --saida" in readme
    r = subprocess.run(
        [sys.executable, "-m", "backend.cli", "gerar", "--modelo", "exemplos/saque-atm.json", "--saida", str(tmp_path)],
        cwd=RAIZ, env=ambiente(), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, r.stderr
    assert all((tmp_path / nome).is_file() for nome in PACOTE)
