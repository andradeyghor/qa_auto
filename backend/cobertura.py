"""Relatório de cobertura dos caminhos gerados: estados, transições e critérios, com o motivo de cada pendência."""
from dataclasses import dataclass

from .caminhos import ResultadoCaminhos
from .schemas import criterios_cobertos, ids_estados


@dataclass(frozen=True)
class Item:
    tipo: str
    nome: str
    motivo: str


@dataclass(frozen=True)
class Cobertura:
    estados: tuple[int, int]
    transicoes: tuple[int, int]
    criterios: tuple[int, int]
    caminhos: int
    caminhos_de_borda: int
    nao_cobertos: tuple[Item, ...] = ()
    bordas_omitidas: tuple[Item, ...] = ()
    avisos: tuple[str, ...] = ()

    @staticmethod
    def percentual(par: tuple[int, int]) -> int:
        cobertos, total = par
        return 100 if total == 0 else round(100 * cobertos / total)

    def resumo(self) -> str:
        partes = [
            f"estados {self.estados[0]}/{self.estados[1]} ({self.percentual(self.estados)}%)",
            f"transições {self.transicoes[0]}/{self.transicoes[1]} ({self.percentual(self.transicoes)}%)",
            f"critérios {self.criterios[0]}/{self.criterios[1]} ({self.percentual(self.criterios)}%)",
        ]
        return f"Cobertura: {', '.join(partes)}; {self.caminhos} caminho(s), {self.caminhos_de_borda} de borda."

    def em_markdown(self) -> str:
        linhas = ["# Cobertura dos caminhos", "", self.resumo(), ""]
        if self.nao_cobertos:
            linhas += ["## Não cobertos", "", "| Tipo | Item | Motivo |", "|---|---|---|"]
            linhas += [f"| {i.tipo} | {_celula(i.nome)} | {_celula(i.motivo)} |" for i in self.nao_cobertos]
            linhas.append("")
        if self.bordas_omitidas:
            linhas += ["## Bordas não geradas", "", "| Comparação | Motivo |", "|---|---|"]
            linhas += [f"| {_celula(i.nome)} | {_celula(i.motivo)} |" for i in self.bordas_omitidas]
            linhas.append("")
        if self.avisos:
            linhas += ["## Avisos", "", *(f"- {a}" for a in self.avisos), ""]
        if not (self.nao_cobertos or self.bordas_omitidas or self.avisos):
            linhas += ["Todos os estados, transições e critérios do modelo foram cobertos.", ""]
        return "\n".join(linhas)


def _celula(texto: str) -> str:
    return " ".join(str(texto).split()).replace("|", "\\|")


def calcular(modelo: dict, resultado: ResultadoCaminhos) -> Cobertura:
    transicoes = modelo["transicoes"]
    estados = ids_estados(modelo)
    visitados = {e for c in resultado.caminhos for e in c.estados()}
    percorridas = {i for c in resultado.caminhos for i in c.indices()}
    todos_criterios = sorted(criterios_cobertos(modelo))
    criterios = {n for i in percorridas for n in transicoes[i].get("criterios") or []}
    motivos = dict(resultado.transicoes_pendentes)

    nao_cobertos = []
    for estado in estados:
        if estado not in visitados:
            chegam = [t["id"] for i, t in enumerate(transicoes) if t["para"] == estado]
            motivo = (
                f"as transições que chegam a ele não foram cobertas ({', '.join(chegam)})" if chegam
                else "nenhuma transição chega a ele"
            )
            nao_cobertos.append(Item("Estado", estado, motivo))
    for i, t in enumerate(transicoes):
        if i not in percorridas:
            nao_cobertos.append(Item("Transição", t["id"], motivos.get(i, "não aparece em nenhum caminho")))
    for n in todos_criterios:
        if n not in criterios:
            ids = [t["id"] for t in transicoes if n in (t.get("criterios") or [])]
            nao_cobertos.append(Item("Critério", f"CA{n}", f"nenhuma transição do critério foi coberta ({', '.join(ids)})"))

    return Cobertura(
        estados=(len([e for e in estados if e in visitados]), len(estados)),
        transicoes=(len(percorridas), len(transicoes)),
        criterios=(len([n for n in todos_criterios if n in criterios]), len(todos_criterios)),
        caminhos=len(resultado.caminhos),
        caminhos_de_borda=sum(c.borda for c in resultado.caminhos),
        nao_cobertos=tuple(nao_cobertos),
        bordas_omitidas=tuple(Item("Borda", p.item, p.motivo) for p in resultado.bordas_omitidas),
        avisos=resultado.avisos,
    )
