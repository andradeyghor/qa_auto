"""Saque em caixa eletrônico: PIN com retenção do cartão e controle de saldo."""
from .base import Catalogo, Definicao, SistemaExemplo

LIMITE_ERROS_PIN = 3
SALDO_INICIAL = 1000
VALOR_SAQUE = 100

CATALOGO = Catalogo(
    estados={
        "AguardandoCartao": "Caixa livre, sem cartão inserido",
        "SemErroPin": "Cartão inserido, aguardando o PIN, sem erros",
        "UmErroPin": "Aguardando o PIN, após um PIN errado",
        "DoisErrosPin": "Aguardando o PIN, após dois PINs errados seguidos",
        "CartaoRetido": "Cartão retido por excesso de PINs errados",
        "MenuPrincipal": "Cliente autenticado, no menu de operações",
        "EntregandoNotas": "Saque aprovado, notas disponíveis para retirada",
    },
    eventos={
        "inserir_cartao": "O cliente insere o cartão",
        "pin_correto": "O cliente informa o PIN correto",
        "pin_incorreto": "O cliente informa um PIN errado",
        "sacar_com_saldo": "O cliente pede um saque dentro do saldo",
        "sacar_sem_saldo": "O cliente pede um saque acima do saldo",
        "retirar_notas": "O cliente retira as notas",
    },
    inicial="AguardandoCartao",
)


class Saque(SistemaExemplo):
    catalogo = CATALOGO

    def __init__(self) -> None:
        self.saldo = SALDO_INICIAL
        self.cartao_inserido = False
        self.autenticado = False
        self.retido = False
        self.notas_pendentes = False
        self.erros_pin = 0

    @property
    def estado(self) -> str:
        if self.retido:
            return "CartaoRetido"
        if self.notas_pendentes:
            return "EntregandoNotas"
        if self.autenticado:
            return "MenuPrincipal"
        if self.cartao_inserido:
            return ("SemErroPin", "UmErroPin", "DoisErrosPin")[self.erros_pin]
        return "AguardandoCartao"

    def inserir_cartao(self) -> bool:
        if self.cartao_inserido:
            return False
        self.cartao_inserido = True
        return True

    def informar_pin(self, correto: bool) -> bool:
        if not self.cartao_inserido or self.autenticado or self.retido:
            return False
        if correto:
            self.autenticado = True
            self.erros_pin = 0
            return True
        self.erros_pin += 1
        if self.erros_pin >= LIMITE_ERROS_PIN:
            self.retido = True
        return True

    def _saque_permitido(self, valor: int) -> bool:
        return valor <= self.saldo

    def sacar(self, valor: int) -> bool:
        """Devolve False quando não há cliente autenticado, há notas pendentes ou o saque é recusado."""
        if not self.autenticado or self.notas_pendentes:
            return False
        if not self._saque_permitido(valor):
            return False
        self.saldo -= valor
        self.notas_pendentes = True
        return True

    def retirar_notas(self) -> bool:
        if not self.notas_pendentes:
            return False
        self.notas_pendentes = False
        self.autenticado = False
        self.cartao_inserido = False
        return True

    def _aplicar(self, evento: str, dados: dict) -> bool:
        if evento == "inserir_cartao":
            return self.inserir_cartao()
        if evento == "pin_correto":
            return self.informar_pin(True)
        if evento == "pin_incorreto":
            return self.informar_pin(False)
        if evento == "sacar_com_saldo":
            return self.sacar(VALOR_SAQUE)
        if evento == "sacar_sem_saldo":
            return self.sacar(self.saldo + VALOR_SAQUE)
        return self.retirar_notas()


class SaqueComBug(Saque):
    """Validação ausente: o saque é liberado mesmo sem saldo."""

    def _saque_permitido(self, valor: int) -> bool:
        return True


def _transicao(id_, de, evento, para, criterios):
    return {"id": id_, "de": de, "evento": evento, "para": para, "guarda": None, "acoes": [], "criterios": criterios}


SAQUE = Definicao(
    nome="Saque em caixa eletrônico",
    catalogo=CATALOGO,
    correto=Saque,
    com_bug=SaqueComBug,
    user_story="Como um correntista,\nQuero sacar dinheiro no caixa eletrônico,\nPara ter dinheiro em espécie.",
    criterios=(
        "1. Saque com saldo suficiente entrega as notas e debita o valor.\n"
        "2. Saque com saldo insuficiente é recusado.\n"
        "3. Cartão é retido após três PINs incorretos."
    ),
    modelo={
        "analise": (
            "Critério 1: com o cliente autenticado, um saque dentro do saldo entrega as notas. "
            "Critério 2: um saque acima do saldo é recusado e o cliente continua no menu. "
            "Critério 3: o terceiro PIN incorreto seguido retém o cartão. "
            "O catálogo não tem variáveis, então os erros de PIN são contados pelos estados "
            "SemErroPin, UmErroPin e DoisErrosPin."
        ),
        "variaveis": [],
        "estados": [
            {"id": "AguardandoCartao", "rotulo": "Aguardando cartão", "tipo": "inicial"},
            {"id": "SemErroPin", "rotulo": "Aguardando PIN, sem erros", "tipo": "intermediario"},
            {"id": "UmErroPin", "rotulo": "Aguardando PIN, um erro", "tipo": "intermediario"},
            {"id": "DoisErrosPin", "rotulo": "Aguardando PIN, dois erros", "tipo": "intermediario"},
            {"id": "CartaoRetido", "rotulo": "Cartão retido", "tipo": "final"},
            {"id": "MenuPrincipal", "rotulo": "Menu principal", "tipo": "intermediario"},
            {"id": "EntregandoNotas", "rotulo": "Entregando notas", "tipo": "intermediario"},
        ],
        "transicoes": [
            _transicao("T1", "AguardandoCartao", "inserir_cartao", "SemErroPin", []),
            _transicao("T2", "SemErroPin", "pin_correto", "MenuPrincipal", []),
            _transicao("T3", "SemErroPin", "pin_incorreto", "UmErroPin", []),
            _transicao("T4", "UmErroPin", "pin_correto", "MenuPrincipal", []),
            _transicao("T5", "UmErroPin", "pin_incorreto", "DoisErrosPin", []),
            _transicao("T6", "DoisErrosPin", "pin_correto", "MenuPrincipal", []),
            _transicao("T7", "DoisErrosPin", "pin_incorreto", "CartaoRetido", [3]),
            _transicao("T8", "MenuPrincipal", "sacar_com_saldo", "EntregandoNotas", [1]),
            _transicao("T9", "MenuPrincipal", "sacar_sem_saldo", "MenuPrincipal", [2]),
            _transicao("T10", "EntregandoNotas", "retirar_notas", "AguardandoCartao", []),
        ],
    },
)
