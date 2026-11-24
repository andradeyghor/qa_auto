"""Contrato comum dos sistemas exemplo usados como alvo dos testes gerados."""
from dataclasses import dataclass, field


class ErroSistema(Exception):
    """Sistema, variante ou evento desconhecido."""


@dataclass(frozen=True)
class Catalogo:
    """Vocabulário do sistema: nome -> descrição de cada estado, evento e variável."""

    estados: dict[str, str]
    eventos: dict[str, str]
    inicial: str
    variaveis: dict[str, str] = field(default_factory=dict)


class SistemaExemplo:
    """Recebe valores de contexto e eventos do catálogo, com dados de entrada, e expõe o estado atual.

    É a interface do adaptador dos testes gerados: `definir_contexto`, `disparar(evento, dados) -> bool` e
    `estado_atual`. O retorno de `disparar` diz se a regra de negócio aceitou o evento, e não só se o estado
    mudou, porque um laço aceito não muda o estado.
    """

    catalogo: Catalogo

    @property
    def estado(self) -> str:
        raise NotImplementedError

    @property
    def estado_atual(self) -> str:
        return self.estado

    def definir_contexto(self, nome: str, valor) -> None:
        if nome not in self.catalogo.variaveis:
            raise ErroSistema(f"Variável de contexto fora do catálogo: {nome}")
        self._definir_contexto(nome, valor)

    def _definir_contexto(self, nome: str, valor) -> None:
        raise ErroSistema(f"O sistema não aceita contexto para a variável: {nome}")

    def disparar(self, evento: str, dados: dict | None = None) -> bool:
        if evento not in self.catalogo.eventos:
            raise ErroSistema(f"Evento fora do catálogo: {evento}")
        return bool(self._aplicar(evento, dict(dados or {})))

    def _aplicar(self, evento: str, dados: dict) -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class Definicao:
    """Tudo o que a ferramenta precisa saber sobre um sistema exemplo."""

    nome: str
    catalogo: Catalogo
    correto: type[SistemaExemplo]
    com_bug: type[SistemaExemplo]
    user_story: str
    criterios: str
    modelo: dict
