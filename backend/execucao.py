"""Execução dos testes gerados em subprocesso, contra as duas variantes do sistema."""
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from .geracao import Artefatos

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
TIMEOUT_EXECUCAO_SEGUNDOS = 60

BUG_DETECTADO = "Bug detectado"
BUG_NAO_DETECTADO = "Bug não detectado"
MODELO_DIVERGE = "Modelo diverge do sistema"
ERRO_EXECUCAO = "Erro de execução"


@dataclass(frozen=True)
class Cenario:
    nome: str
    passou: bool
    motivo: str = ""


@dataclass(frozen=True)
class ResultadoVariante:
    variante: str
    cenarios: list[Cenario] = field(default_factory=list)
    erro: str = ""

    @property
    def falhas(self) -> list[Cenario]:
        return [c for c in self.cenarios if not c.passou]


@dataclass(frozen=True)
class Execucao:
    veredito: str
    correto: ResultadoVariante
    bug: ResultadoVariante


def _nome_legivel(nome: str) -> str:
    return nome.removeprefix("test_").replace("__", " - ").replace("_", " ").capitalize()


def _motivo(texto: str) -> str:
    return texto.splitlines()[0].removeprefix("AssertionError: ") if texto else ""


def _ler_junit(caminho: Path, variante: str) -> ResultadoVariante:
    """Lê o JUnit XML. Qualquer teste que não chegou a executar invalida a variante."""
    if not caminho.exists():
        return ResultadoVariante(variante, erro="O pytest não produziu resultado.")
    cenarios = []
    for caso in ET.parse(caminho).getroot().iter("testcase"):
        for problema in caso.findall("error") + caso.findall("skipped"):
            return ResultadoVariante(variante, erro=_motivo(problema.get("message", "Erro na coleta.")))
        falha = caso.find("failure")
        motivo = _motivo(falha.get("message", "")) if falha is not None else ""
        cenarios.append(Cenario(_nome_legivel(caso.get("name", "")), falha is None, motivo))
    if not cenarios:
        return ResultadoVariante(variante, erro="Nenhum teste foi coletado.")
    return ResultadoVariante(variante, cenarios)


def _executar_variante(pasta: Path, variante: str, timeout: float) -> ResultadoVariante:
    relatorio = pasta / f"resultado_{variante}.xml"
    ambiente = {
        **os.environ,
        "QA_VARIANTE": variante,
        "PYTHONPATH": str(RAIZ_PROJETO),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    comando = [
        sys.executable, "-m", "pytest", str(pasta), "-q",
        "-p", "no:cacheprovider", f"--rootdir={pasta}", f"--junitxml={relatorio}",
    ]
    try:
        subprocess.run(comando, cwd=pasta, env=ambiente, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ResultadoVariante(variante, erro=f"A execução ultrapassou {timeout:g}s.")
    return _ler_junit(relatorio, variante)


def calcular_veredito(correto: ResultadoVariante, bug: ResultadoVariante) -> str:
    """A variante correta é a referência da verdade: falha nela indica erro do modelo."""
    if correto.erro:
        return ERRO_EXECUCAO
    if correto.falhas:
        return MODELO_DIVERGE
    if bug.erro:
        return ERRO_EXECUCAO
    return BUG_DETECTADO if bug.falhas else BUG_NAO_DETECTADO


def executar_testes(artefatos: Artefatos, timeout: float = TIMEOUT_EXECUCAO_SEGUNDOS) -> Execucao:
    """Grava o pacote completo (feature, teste, adaptador e conftest) e roda as duas variantes."""
    with tempfile.TemporaryDirectory(prefix="qa_auto_", ignore_cleanup_errors=True) as temporaria:
        pasta = Path(temporaria)
        for nome, conteudo in artefatos.arquivos().items():
            (pasta / nome).write_text(conteudo, encoding="utf-8")
        correto = _executar_variante(pasta, "correto", timeout)
        bug = _executar_variante(pasta, "bug", timeout)
    return Execucao(calcular_veredito(correto, bug), correto, bug)
