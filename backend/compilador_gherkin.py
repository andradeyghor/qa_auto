"""Compilador dos caminhos em Gherkin (`# language: pt`) com o vocabulário fixo de seis frases.

As mesmas frases geram as definições de passo do teste (`pacote.py`), então todo passo tem definição por
construção. Texto do modelo só entra no `.feature`, normalizado para não alterar a estrutura do arquivo.
"""
import re

from gherkin.errors import ParserError
from gherkin.parser import Parser

from . import expressoes
from .caminhos import Caminho, formatar_valor

# As seis frases, sem a palavra-chave. Os campos são preenchidos aqui e lidos por `parsers.parse` no teste.
ESTADO_INICIAL = 'que o sistema está no estado "{estado}"'
CONTEXTO = 'que o contexto "{variavel}" vale {valor}'
EVENTO = 'ocorre o evento "{evento}"'
EVENTO_COM_DADOS = 'ocorre o evento "{evento}" com:'
ESTADO = 'o sistema está no estado "{estado}"'
RECUSA = 'o evento é recusado e o sistema permanece no estado "{estado}"'
FRASES = (ESTADO_INICIAL, CONTEXTO, EVENTO, EVENTO_COM_DADOS, ESTADO, RECUSA)


class ErroGherkin(ValueError):
    """O `.feature` não passou no parser Gherkin oficial."""


def limpar(texto) -> str:
    """Impede que texto do modelo altere a estrutura do Gherkin (aspas e quebras de linha)."""
    return re.sub(r"\s+", " ", str(texto)).replace('"', "'").strip()


def _celula(texto) -> str:
    return limpar(texto).replace("\\", "\\\\").replace("|", "\\|")


def guarda_legivel(guarda: str) -> str:
    """Guarda em forma canônica (operadores com espaços), ou o texto original se não for analisável."""
    try:
        return expressoes.formatar(guarda)
    except expressoes.ErroExpressao:
        return re.sub(r"\s*([<>!=]=|[<>])\s*", r" \1 ", guarda)


def nome_do_cenario(numero: int, caminho: Caminho) -> str:
    """'Caminho N: evento → evento → EstadoFinal'."""
    return f"Caminho {numero}: " + " → ".join([*(limpar(p.evento) for p in caminho.passos), limpar(caminho.final)])


def tags(numero: int, caminho: Caminho, modelo: dict) -> list[str]:
    criterios = caminho.criterios(modelo)
    resultado = [*(f"@CA-{n}" for n in criterios), f"@caminho-{numero}"]
    if not criterios:
        resultado.append("@auxiliar")
    if caminho.borda:
        resultado.append("@borda")
    return resultado


def gerar_feature(modelo: dict, caminhos, titulo: str) -> str:
    """Um cenário por caminho: estado inicial e contexto em Dado/E, cada evento em Quando, cada estado em Então."""
    transicoes = modelo["transicoes"]
    linhas = ["# language: pt", f"Funcionalidade: {limpar(titulo) or 'Modelo gerado'}"]
    for numero, caminho in enumerate(caminhos, start=1):
        linhas += ["", "  " + " ".join(tags(numero, caminho, modelo)), f"  Cenário: {nome_do_cenario(numero, caminho)}"]
        linhas.append("    Dado " + ESTADO_INICIAL.format(estado=limpar(caminho.inicial)))
        for nome, valor in caminho.contexto:
            linhas.append("    E " + CONTEXTO.format(variavel=limpar(nome), valor=limpar(formatar_valor(valor))))
        for passo in caminho.passos:
            if passo.aceito:
                guarda = transicoes[passo.transicao].get("guarda")
                if guarda:
                    linhas.append(f"    # guarda: {limpar(guarda_legivel(guarda))}")
            else:
                linhas.append(f"    # recusado: nenhuma transição de {limpar(passo.estado)} aceita estes dados")
            if passo.dados:
                linhas.append("    Quando " + EVENTO_COM_DADOS.format(evento=limpar(passo.evento)))
                linhas += [f"      | {_celula(n)} | {_celula(formatar_valor(v))} |" for n, v in passo.dados]
            else:
                linhas.append("    Quando " + EVENTO.format(evento=limpar(passo.evento)))
            frase = ESTADO if passo.aceito else RECUSA
            linhas.append("    Então " + frase.format(estado=limpar(passo.estado)))
    return "\n".join(linhas) + "\n"


def validar_feature(texto: str) -> dict:
    """Documento do parser Gherkin oficial; ErroGherkin se o arquivo não for aceito."""
    try:
        return Parser().parse(texto)
    except ParserError as e:
        raise ErroGherkin(str(e)) from e
