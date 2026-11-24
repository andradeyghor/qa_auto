"""Linha de comando: gera os artefatos de teste a partir de um modelo JSON ou de um arquivo de requisitos.

    python -m backend.cli gerar --modelo exemplos/saque-atm.json --saida saida/saque-atm
    python -m backend.cli gerar --requisito requisito.md --motor ollama --sistema login --saida saida/login

A extração usa `backend.servico` diretamente, sem a API HTTP. O diretório de saída recebe o pacote completo:
modelo JSON, diagrama Mermaid, `.feature`, teste, adaptador, `conftest.py`, cobertura e `LEIAME.md`.
"""
import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from sistemas_exemplo import SISTEMAS, obter

from . import servico
from .caminhos import ESTRATEGIAS, TRANSICOES
from .entrada import ErroImportacao, extrair_requisitos_de_texto, numerar_criterios
from .geracao import SLUG_LIVRE, Artefatos, gerar_artefatos, normalizar_slug
from .llm import ErroLLM
from .schemas import ModeloEstados, Requisicao
from .validacao import ErroModelo, descrever, erros_de_esquema, validar_modelo


class ErroCli(Exception):
    """Entrada inválida ou falha na geração, com a mensagem para quem usa a linha de comando."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m backend.cli", description="Geração de testes do QUALITY ASSURANCE CONSULTANT, sem interface web."
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    gerar = comandos.add_parser("gerar", help="Gera o pacote de testes a partir de um modelo ou de um requisito.")
    origem = gerar.add_mutually_exclusive_group(required=True)
    origem.add_argument("--modelo", type=Path, help="Modelo de estados em JSON (ou gabarito com 'modelo').")
    origem.add_argument("--requisito", type=Path, help="Arquivo com as seções '# História' e '# Critérios'.")
    gerar.add_argument("--motor", help="Provedor do LLM para extrair o modelo (obrigatório com --requisito).")
    gerar.add_argument("--sistema", choices=list(SISTEMAS), help="Sistema exemplo alvo; sem ele, o adaptador é um esqueleto.")
    gerar.add_argument("--estrategia", choices=list(ESTRATEGIAS), default=TRANSICOES, help="Estratégia de caminhos.")
    gerar.add_argument("--sem-borda", action="store_true", help="Não gera os cenários de borda.")
    gerar.add_argument("--saida", type=Path, required=True, help="Diretório onde o pacote é gravado.")
    return parser


def ler_modelo(caminho: Path, sistema: str | None) -> tuple[dict, str, str | None]:
    """Modelo validado, slug e título. Um gabarito de `exemplos/` traz também o nome e os critérios."""
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise ErroCli(f"Não foi possível ler o modelo {caminho}: {e}") from e
    gabarito = isinstance(dados, dict) and isinstance(dados.get("modelo"), dict)
    bruto = dados["modelo"] if gabarito else dados
    try:
        modelo = ModeloEstados.model_validate(bruto)
    except ValidationError as e:
        raise ErroCli(f"O modelo {caminho} não segue o esquema:\n{descrever(erros_de_esquema(e))}") from e
    criterios = dados.get("criterios", "") if gabarito else ""
    erros = validar_modelo(modelo, criterios, obter(sistema).catalogo if sistema else None)
    if erros:
        raise ErroCli(f"O modelo {caminho} tem erros:\n{descrever(erros)}")
    return modelo.model_dump(), normalizar_slug(caminho.stem), dados.get("nome") if gabarito else None


def extrair_modelo(caminho: Path, motor: str, sistema: str | None) -> tuple[dict, servico.ResultadoGeracao]:
    """Modelo extraído pelo provedor a partir do arquivo de requisitos."""
    try:
        historia, criterios = extrair_requisitos_de_texto(caminho.read_text(encoding="utf-8-sig"))
    except OSError as e:
        raise ErroCli(f"Não foi possível ler o requisito {caminho}: {e}") from e
    except ErroImportacao as e:
        raise ErroCli(str(e)) from e
    try:
        requisicao = Requisicao(user_story=historia, criterios=numerar_criterios(criterios), motor=motor, sistema=sistema)
    except ValidationError as e:
        raise ErroCli("; ".join(str(err["msg"]).replace("Value error, ", "") for err in e.errors())) from e
    try:
        resultado = servico.gerar(requisicao)
    except (ErroLLM, ErroModelo, servico.ErroOrcamento) as e:
        raise ErroCli(f"A extração do modelo falhou: {e}") from e
    return resultado.modelo.model_dump(), resultado


def gravar(artefatos: Artefatos, saida: Path) -> list[Path]:
    saida.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for nome, conteudo in artefatos.arquivos().items():
        destino = saida / nome
        destino.write_text(conteudo, encoding="utf-8", newline="\n")
        caminhos.append(destino)
    return caminhos


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(errors="replace")  # consoles sem UTF-8 (ex.: cp1252 no Windows)
    parser = _parser()
    args = parser.parse_args(argv)
    if args.requisito and not args.motor:
        parser.error("--motor é obrigatório com --requisito")
    try:
        if args.modelo:
            modelo, slug, titulo = ler_modelo(args.modelo, args.sistema)
        else:
            modelo, resultado = extrair_modelo(args.requisito, args.motor, args.sistema)
            slug, titulo = SLUG_LIVRE, None
            print(
                f"Modelo extraído por {resultado.provedor} ({resultado.modelo_llm}) em "
                f"{len(resultado.tentativas)} tentativa(s), {resultado.duracao:.1f}s."
            )
        artefatos = gerar_artefatos(
            modelo, args.sistema, slug=slug, titulo=titulo, estrategia=args.estrategia, bordas=not args.sem_borda
        )
        arquivos = gravar(artefatos, args.saida)
    except ErroCli as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    print(f"Pacote gravado em {args.saida}:")
    for arquivo in arquivos:
        print(f"  {arquivo.name}")
    print(artefatos.cobertura.resumo())
    print(f"Para rodar, a partir da raiz do projeto: python -m pytest {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
