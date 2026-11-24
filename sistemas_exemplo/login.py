"""Login bancário: autenticação com bloqueio após três senhas erradas."""
from .base import Catalogo, Definicao, SistemaExemplo

LIMITE_FALHAS = 3

CATALOGO = Catalogo(
    estados={
        "SemFalha": "Deslogado, sem nenhuma senha errada",
        "UmaFalha": "Deslogado, após uma senha errada",
        "DuasFalhas": "Deslogado, após duas senhas erradas seguidas",
        "ContaBloqueada": "Conta bloqueada por excesso de tentativas",
        "Dashboard": "Autenticado, no painel da conta",
    },
    eventos={
        "senha_correta": "O cliente informa a senha correta",
        "senha_incorreta": "O cliente informa uma senha errada",
    },
    inicial="SemFalha",
)


class Login(SistemaExemplo):
    catalogo = CATALOGO

    def __init__(self) -> None:
        self.falhas = 0
        self.autenticado = False
        self.bloqueada = False

    @property
    def estado(self) -> str:
        if self.bloqueada:
            return "ContaBloqueada"
        if self.autenticado:
            return "Dashboard"
        return ("SemFalha", "UmaFalha", "DuasFalhas")[min(self.falhas, 2)]

    def _deve_bloquear(self) -> bool:
        return self.falhas >= LIMITE_FALHAS

    def autenticar(self, senha_correta: bool) -> bool:
        """Devolve False quando a conta já está bloqueada ou o cliente já entrou."""
        if self.bloqueada or self.autenticado:
            return False
        if senha_correta:
            self.autenticado = True
            self.falhas = 0
            return True
        self.falhas += 1
        self.bloqueada = self._deve_bloquear()
        return True

    def _aplicar(self, evento: str, dados: dict) -> bool:
        return self.autenticar(evento == "senha_correta")


class LoginComBug(Login):
    """Erro de limite: a terceira senha errada não bloqueia a conta."""

    def _deve_bloquear(self) -> bool:
        return self.falhas > LIMITE_FALHAS


def _transicao(id_, de, evento, para, criterios):
    return {"id": id_, "de": de, "evento": evento, "para": para, "guarda": None, "acoes": [], "criterios": criterios}


LOGIN = Definicao(
    nome="Login bancário",
    catalogo=CATALOGO,
    correto=Login,
    com_bug=LoginComBug,
    user_story="Como um cliente bancário,\nQuero realizar o login no sistema,\nPara acessar minha conta corrente.",
    criterios=(
        "1. Senha correta redireciona para o Dashboard.\n"
        "2. Senha incorreta exibe mensagem de erro.\n"
        "3. Três tentativas erradas bloqueiam a conta."
    ),
    modelo={
        "analise": (
            "Critério 1: senha correta leva ao Dashboard a partir de qualquer estado deslogado. "
            "Critério 2: senha incorreta mantém o cliente deslogado e conta a falha. "
            "Critério 3: a terceira senha incorreta seguida bloqueia a conta. "
            "O catálogo não tem variáveis, então a contagem é representada pelos estados "
            "SemFalha, UmaFalha e DuasFalhas."
        ),
        "variaveis": [],
        "estados": [
            {"id": "SemFalha", "rotulo": "Sem falha", "tipo": "inicial"},
            {"id": "UmaFalha", "rotulo": "Uma falha", "tipo": "intermediario"},
            {"id": "DuasFalhas", "rotulo": "Duas falhas", "tipo": "intermediario"},
            {"id": "ContaBloqueada", "rotulo": "Conta bloqueada", "tipo": "final"},
            {"id": "Dashboard", "rotulo": "Dashboard", "tipo": "final"},
        ],
        "transicoes": [
            _transicao("T1", "SemFalha", "senha_correta", "Dashboard", [1]),
            _transicao("T2", "SemFalha", "senha_incorreta", "UmaFalha", [2]),
            _transicao("T3", "UmaFalha", "senha_correta", "Dashboard", [1]),
            _transicao("T4", "UmaFalha", "senha_incorreta", "DuasFalhas", [2]),
            _transicao("T5", "DuasFalhas", "senha_correta", "Dashboard", [1]),
            _transicao("T6", "DuasFalhas", "senha_incorreta", "ContaBloqueada", [3]),
        ],
    },
)
