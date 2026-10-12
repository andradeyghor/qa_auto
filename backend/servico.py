"""Orquestração do passo 1: prompt -> LLM -> validação, com retry e feedback do erro."""
from .llm import chamar_llm
from .prompts import SYSTEM_PROMPT, montar_prompt_correcao, montar_user_prompt
from .schemas import ModeloMBT, Requisicao
from .validacao import ErroModelo, validar_resposta

MAX_TENTATIVAS = 3


def gerar_modelo(req: Requisicao, chamar=chamar_llm) -> ModeloMBT:
    mensagens = [{"role": "user", "content": montar_user_prompt(req.user_story, req.criterios)}]
    ultimo_erro = ""
    for _ in range(MAX_TENTATIVAS):
        resposta = chamar(req.motor, SYSTEM_PROMPT, mensagens)
        try:
            return validar_resposta(resposta, req.criterios)
        except ErroModelo as e:
            ultimo_erro = str(e)
            mensagens.append({"role": "assistant", "content": resposta})
            mensagens.append({"role": "user", "content": montar_prompt_correcao(ultimo_erro)})
    raise ErroModelo(
        f"Não foi possível obter um modelo válido após {MAX_TENTATIVAS} tentativas. "
        f"Último erro: {ultimo_erro}"
    )
