"""Geração determinística dos artefatos a partir do modelo, sem uso do LLM.

Caminhos viáveis (`caminhos`), cobertura (`cobertura`), Gherkin em português (`compilador_gherkin`) e o pacote
executável com teste, adaptador e conftest (`gerador_pytest`). Este módulo junta tudo em `Artefatos`.
"""
import io
import json
import re
import unicodedata
import zipfile
from dataclasses import dataclass, replace

from sistemas_exemplo import obter

from . import gerador_pytest
from .caminhos import TRANSICOES, Caminho, Limites, gerar_caminhos
from .cobertura import Cobertura, calcular
from .compilador_gherkin import gerar_feature, guarda_legivel
from .gerador_pytest import ESQUELETO, SIMULACAO, SISTEMA
from .schemas import estado_inicial, estados_finais, rotulos

SLUG_LIVRE = "requisito"
TITULO_LIVRE = "Modelo gerado"
DATA_ZIP = (1980, 1, 1, 0, 0, 0)  # data fixa nas entradas do zip, para o pacote ser idêntico a cada geração


@dataclass(frozen=True)
class Artefatos:
    slug: str
    titulo: str
    feature: str
    script: str
    adaptador: str
    conftest: str
    leiame: str
    modelo_json: str
    diagrama: str
    cobertura: Cobertura
    caminhos: tuple[Caminho, ...] = ()

    @property
    def modulo(self) -> str:
        return self.slug.replace("-", "_")

    @property
    def nome_feature(self) -> str:
        return f"{self.slug}.feature"

    @property
    def nome_script(self) -> str:
        return f"test_{self.modulo}.py"

    @property
    def nome_adaptador(self) -> str:
        return f"adaptador_{self.modulo}.py"

    @property
    def nome_modelo(self) -> str:
        return f"{self.slug}.json"

    @property
    def nome_diagrama(self) -> str:
        return f"{self.slug}.mmd"

    @property
    def nome_zip(self) -> str:
        return f"{self.slug}.zip"

    def arquivos(self) -> dict[str, str]:
        """Conteúdo do pacote, por nome de arquivo."""
        return {
            self.nome_feature: self.feature,
            self.nome_script: self.script,
            self.nome_adaptador: self.adaptador,
            "conftest.py": self.conftest,
            "LEIAME.md": self.leiame,
            self.nome_modelo: self.modelo_json,
            self.nome_diagrama: self.diagrama,
            "cobertura.md": self.cobertura.em_markdown(),
        }

    def zip(self) -> bytes:
        """Pacote zip com uma pasta `<slug>/`, pronto para descompactar na raiz do projeto."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as arquivo_zip:
            for nome, conteudo in self.arquivos().items():
                info = zipfile.ZipInfo(f"{self.slug}/{nome}", date_time=DATA_ZIP)
                info.compress_type = zipfile.ZIP_DEFLATED
                arquivo_zip.writestr(info, conteudo.encode("utf-8"))
        return buffer.getvalue()


def normalizar_slug(texto: str | None) -> str:
    """Id em minúsculas ASCII com hífens (ex.: 'Cupom Promocional' -> 'cupom-promocional')."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-") or SLUG_LIVRE


def _rotulo_mermaid(texto: str) -> str:
    """Remove do rótulo os caracteres que mudam a sintaxe do Mermaid (`:`, `;`, `"`, `#`, chaves, quebras)."""
    texto = re.sub(r'[:;"#{}]', " ", texto)
    return re.sub(r"\s+", " ", texto).strip() or "evento"


def modelo_para_mermaid(modelo: dict) -> str:
    """Converte o modelo em stateDiagram-v2: rótulos dos estados, evento [guarda] (CA<n>) e finais."""
    linhas = ["stateDiagram-v2"]
    for id_, rotulo in rotulos(modelo).items():
        linhas.append(f'    state "{_rotulo_mermaid(rotulo)}" as {id_}')
    linhas.append(f"    [*] --> {estado_inicial(modelo)}")
    for t in modelo["transicoes"]:
        rotulo = _rotulo_mermaid(t["evento"])
        if t.get("guarda"):
            rotulo += f" [{_rotulo_mermaid(guarda_legivel(t['guarda']))}]"
        if t.get("criterios"):
            rotulo += " (" + ", ".join(f"CA{n}" for n in t["criterios"]) + ")"
        linhas.append(f"    {t['de']} --> {t['para']} : {rotulo}")
    linhas.extend(f"    {final} --> [*]" for final in estados_finais(modelo))
    return "\n".join(linhas)


def gerar_artefatos(
    modelo: dict,
    sistema_id: str | None = None,
    *,
    slug: str | None = None,
    titulo: str | None = None,
    estrategia: str = TRANSICOES,
    bordas: bool = True,
    limites: Limites | None = None,
    adaptador: str | None = None,
) -> Artefatos:
    """Caminhos, Gherkin, teste, adaptador e conftest do modelo, de forma determinística.

    Com `sistema_id`, o adaptador usa o sistema exemplo; sem ele, é um esqueleto. `adaptador="simulacao"`
    troca o adaptador pela simulação do próprio modelo, usada para testar o gerador.
    """
    definicao = obter(sistema_id) if sistema_id else None
    slug = normalizar_slug(slug or sistema_id or SLUG_LIVRE)
    titulo = titulo or (definicao.nome if definicao else TITULO_LIVRE)
    modo = adaptador or (SISTEMA if sistema_id else ESQUELETO)
    if modo not in (SISTEMA, ESQUELETO, SIMULACAO) or (modo == SISTEMA and not sistema_id):
        raise ValueError(f"Adaptador inválido: {modo}")

    resultado = gerar_caminhos(modelo, estrategia, bordas, limites)
    # Os nomes dos arquivos saem do slug; o código do pacote é preenchido em seguida
    base = Artefatos(
        slug=slug,
        titulo=titulo,
        feature=gerar_feature(modelo, resultado.caminhos, titulo),
        script="",
        adaptador="",
        conftest="",
        leiame="",
        modelo_json=json.dumps(modelo, ensure_ascii=False, indent=2) + "\n",
        diagrama=modelo_para_mermaid(modelo) + "\n",
        cobertura=calcular(modelo, resultado),
        caminhos=resultado.caminhos,
    )
    nomes = {
        "__FEATURE__": base.nome_feature,
        "__SCRIPT__": base.nome_script,
        "__ADAPTADOR__": base.nome_adaptador,
        "__MODELO__": base.nome_modelo,
        "__DIAGRAMA__": base.nome_diagrama,
    }
    return replace(
        base,
        script=gerador_pytest.gerar_script(base.nome_feature, modo),
        adaptador=gerador_pytest.gerar_adaptador(modo, sistema_id, base.nome_modelo),
        conftest=gerador_pytest.gerar_conftest(base.nome_adaptador.removesuffix(".py")),
        leiame=gerador_pytest.gerar_leiame(titulo, nomes, modo, sistema_id),
    )
