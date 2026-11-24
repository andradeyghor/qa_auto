from pathlib import Path

import pytest
import requests
from streamlit.testing.v1 import AppTest

import demo_data
import exemplos
from backend.servico import espera_maxima
from sistemas_exemplo import obter

APP = str(Path(__file__).resolve().parent.parent / "app.py")
SAQUE = "Saque em caixa eletrônico"
LOGIN = "Login bancário"
AVISO_DEMO = "Demonstração: modelo de referência, sem LLM"


class RespostaFalsa:
    def __init__(self, dados=None, status_code=200, texto=None):
        self.dados = dados
        self.status_code = status_code
        self.text = texto if texto is not None else ""

    def json(self):
        if self.dados is None:
            raise requests.JSONDecodeError("Expecting value", self.text, 0)
        return self.dados


def resposta_gerar(modelo, tentativas=1, duracao=1.5):
    return RespostaFalsa({"modelo": modelo, "tentativas": tentativas, "duracao": duracao, "historico": []})


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    return at


@pytest.fixture
def backend_falso(monkeypatch):
    """Substitui o POST ao backend; guarda o que foi enviado e o timeout usado."""
    estado = {"resposta": resposta_gerar(obter("login").modelo), "enviado": {}, "chamadas": 0}

    def post(url, json, timeout):
        estado["chamadas"] += 1
        estado["enviado"] = dict(json)
        estado["timeout"] = timeout
        if isinstance(estado["resposta"], Exception):
            raise estado["resposta"]
        return estado["resposta"]

    monkeypatch.setattr(requests, "post", post)
    return estado


def modo_real(at):
    at.toggle[0].set_value(False).run()
    return at


def gerar(at):
    at.button(key="gerar").click().run()
    assert not at.exception
    return at


def codigos(at):
    return "\n".join(c.value for c in at.code)


def textos(elementos):
    return "\n".join(e.value for e in elementos)


def downloads(at):
    return at.get("download_button")


# dados
def test_exemplos_sem_artefatos_fixos():
    for exemplo in demo_data.EXEMPLOS.values():
        assert set(exemplo) == {"sistema", "gabarito", "user_story", "criterios"}
        assert demo_data.modelo_de_referencia(next(n for n, e in demo_data.EXEMPLOS.items() if e is exemplo))
    assert "assert True" not in Path(demo_data.__file__).read_text(encoding="utf-8")


def test_exemplos_canonicos_disponiveis():
    nomes = set(demo_data.EXEMPLOS)
    assert {LOGIN, SAQUE, "Cupom Promocional", "Autenticação MFA", "Carrinho de Compras"} <= nomes


# 3.5 exemplos em 1 clique
@pytest.mark.parametrize("nome", list(demo_data.EXEMPLOS))
def test_carregar_exemplo_preenche_sem_gerar(app, backend_falso, nome):
    app.selectbox(key="exemplo").select(nome).run()
    assert not app.exception
    exemplo = demo_data.EXEMPLOS[nome]
    assert app.text_area(key="user_story").value == exemplo["user_story"]
    assert app.text_area(key="criterios").value == exemplo["criterios"]
    assert app.selectbox(key="sistema_alvo").value == (exemplo["sistema"] or "")
    assert "resultado" not in app.session_state
    assert backend_falso["chamadas"] == 0


def test_exemplo_continua_editavel(app):
    app.selectbox(key="exemplo").select("Cupom Promocional").run()
    app.text_area(key="criterios").set_value("1. outro").run()
    assert app.text_area(key="criterios").value == "1. outro"


# seletor
def test_carregar_exemplo_seleciona_sistema(app):
    assert app.selectbox(key="sistema_alvo").value == "login"
    app.selectbox(key="exemplo").select(SAQUE).run()
    assert app.selectbox(key="sistema_alvo").value == "saque"


# artefatos (add-mbt-generator 4.1: modelo, diagrama, feature, teste, adaptador e pacote zip)
DOWNLOADS = 6


def test_demo_gera_artefatos_do_modelo_de_referencia(app):
    gerar(app)
    assert "# language: pt\nFuncionalidade: Login bancário" in codigos(app)
    assert 'scenarios("login.feature")' in codigos(app)
    assert 'criar("login", os.getenv("QA_VARIANTE", "correto"))' in codigos(app)
    assert len(downloads(app)) == DOWNLOADS
    assert app.session_state["resultado"]["artefatos"].nome_script == "test_login.py"


# 2.3 novo corpo do /gerar
def test_modo_real_com_backend_falso(app, backend_falso):
    backend_falso["resposta"] = resposta_gerar(obter("login").modelo, tentativas=2, duracao=42.0)
    modo_real(app)
    gerar(app)
    assert backend_falso["enviado"]["sistema"] == "login"
    assert "Funcionalidade: Login bancário" in codigos(app)
    assert len(downloads(app)) == DOWNLOADS
    assert app.session_state["resultado"]["tentativas"] == 2
    assert any("2 tentativa(s) em 42.0s" in c.value for c in app.caption)


def test_modo_real_sem_sistema_gera_esqueleto(app, backend_falso):
    modo_real(app)
    app.selectbox(key="sistema_alvo").select("").run()
    gerar(app)
    assert backend_falso["enviado"]["sistema"] is None
    assert any("esqueletos" in i.value for i in app.info)
    assert 'scenarios("login.feature")' in codigos(app)
    assert "Implemente o adaptador do sistema sob teste" in codigos(app)
    assert not [b for b in app.button if b.key == "executar"]


def test_texto_editado_usa_o_slug_de_texto_livre(app, backend_falso):
    modo_real(app)
    app.text_area(key="criterios").set_value(obter("login").criterios + "\n4. Novo critério.").run()
    gerar(app)
    assert app.session_state["resultado"]["artefatos"].nome_feature == "requisito.feature"
    assert "Funcionalidade: Login bancário" in codigos(app)  # título do sistema alvo


def test_abas_gherkin_pytest_e_cobertura_no_modo_real(app, backend_falso):
    cupom = exemplos.carregar("cupom-promocional")["modelo"]
    backend_falso["resposta"] = resposta_gerar(cupom)
    app.selectbox(key="exemplo").select("Cupom Promocional").run()
    modo_real(app)
    gerar(app)
    artefatos = app.session_state["resultado"]["artefatos"]
    assert "Funcionalidade: Cupom Promocional" in codigos(app)
    assert codigos(app).count("Cenário: Caminho") == len(artefatos.caminhos)
    assert 'scenarios("cupom-promocional.feature")' in codigos(app)
    assert any(c.value.startswith("Cobertura: estados 5/5 (100%)") for c in app.caption)
    caminhos = next(d.value for d in app.dataframe if "Transições" in d.value.columns)
    assert len(caminhos) == len(artefatos.caminhos)
    assert set(caminhos["Critérios"]) >= {"1, 3, 4"}


# 4.4 estratégia e cenários de borda
def test_sem_cenarios_de_borda(app):
    app.selectbox(key="exemplo").select("Cupom Promocional").run()
    gerar(app)
    assert "@borda" in codigos(app)
    app.checkbox(key="bordas").uncheck().run()
    gerar(app)
    assert "@borda" not in codigos(app)


def test_estrategia_de_caminhos_elementares(app):
    app.selectbox(key="exemplo").select("Carrinho de Compras").run()
    gerar(app)
    por_transicoes = len(app.session_state["resultado"]["artefatos"].caminhos)
    app.selectbox(key="estrategia").select("elementares").run()
    gerar(app)
    assert len(app.session_state["resultado"]["artefatos"].caminhos) > por_transicoes


def test_exemplo_usa_pipeline_real_fora_da_demo(app, backend_falso):
    app.selectbox(key="exemplo").select("Cupom Promocional").run()
    modo_real(app)
    gerar(app)
    assert backend_falso["chamadas"] == 1
    assert backend_falso["enviado"]["criterios"] == demo_data.EXEMPLOS["Cupom Promocional"]["criterios"]


# 2.4 espera e tratamento de erros
def test_front_espera_o_orcamento(app, backend_falso, monkeypatch):
    monkeypatch.setenv("QA_ORCAMENTO_GERACAO", "100")
    modo_real(app)
    gerar(app)
    assert backend_falso["timeout"] == espera_maxima() == 115


def test_erro_500_em_texto_puro(app, backend_falso):
    backend_falso["resposta"] = RespostaFalsa(status_code=500, texto="Internal Server Error")
    modo_real(app)
    gerar(app)
    assert "Erro interno no servidor (status 500)" in textos(app.error)
    assert "resultado" not in app.session_state


def test_erro_json_mostra_mensagem(app, backend_falso):
    backend_falso["resposta"] = RespostaFalsa(
        {"codigo": "orcamento_esgotado", "mensagem": "O orçamento de 180s se esgotou."}, status_code=504
    )
    modo_real(app)
    gerar(app)
    assert "O orçamento de 180s se esgotou. (status 504)" in textos(app.error)


def test_backend_desligado(app, backend_falso):
    backend_falso["resposta"] = requests.ConnectionError("recusado")
    modo_real(app)
    gerar(app)
    erro = textos(app.error)
    assert "indisponível" in erro and "uvicorn backend.main:app" in erro


def test_resposta_200_inesperada(app, backend_falso):
    backend_falso["resposta"] = RespostaFalsa(texto="<html>proxy</html>")
    modo_real(app)
    gerar(app)
    assert "formato inesperado" in textos(app.error)


# 3.1 numeração dos critérios
def test_criterios_sem_numero_sao_numerados_e_enviados(app, backend_falso):
    modo_real(app)
    app.text_area(key="criterios").set_value("Senha correta entra\nSenha errada mostra erro\nTrês erros bloqueiam").run()
    previa = textos(app.markdown)
    assert "1\\. Senha correta entra" in previa and "3\\. Três erros bloqueiam" in previa
    gerar(app)
    assert backend_falso["enviado"]["criterios"] == (
        "1. Senha correta entra\n2. Senha errada mostra erro\n3. Três erros bloqueiam"
    )


# 3.3 importação de arquivo e edição posterior
ARQUIVO = (
    "# História\nComo cliente, quero sacar.\n\n# Critérios\n"
    "1. cada tentativa inválida incrementa o contador\n2. três erros retêm o cartão\n"
).encode("utf-8")


def test_importacao_preenche_os_campos(app):
    app.get("file_uploader")[0].upload("req.md", ARQUIVO, "text/markdown").run()
    assert not app.exception
    assert app.text_area(key="user_story").value == "Como cliente, quero sacar."
    assert "1. cada tentativa inválida incrementa o contador" in app.text_area(key="criterios").value
    assert "req.md" in textos(app.success)


def test_edicao_apos_importar_prevalece(app, backend_falso):
    modo_real(app)
    app.get("file_uploader")[0].upload("req.md", ARQUIVO, "text/markdown").run()
    app.text_area(key="criterios").set_value("1. cada tentativa inválida incrementa\n2. critério editado").run()
    gerar(app)
    assert backend_falso["enviado"]["criterios"] == "1. cada tentativa inválida incrementa\n2. critério editado"
    assert app.text_area(key="criterios").value.endswith("critério editado")


def test_arquivo_sem_historia(app):
    app.get("file_uploader")[0].upload("req.md", b"# Criterios\n1. a\n", "text/markdown").run()
    erro = textos(app.error)
    assert "história de usuário não foi encontrada" in erro
    assert "# História" in erro  # mostra o formato aceito
    assert app.text_area(key="user_story").value == obter("login").user_story


# 3.4 campos obrigatórios e limite
def test_envio_sem_criterios_bloqueado(app, backend_falso):
    modo_real(app)
    app.text_area(key="criterios").set_value("   ").run()
    gerar(app)
    assert "critérios de aceite são obrigatórios" in textos(app.error)
    assert backend_falso["chamadas"] == 0


def test_envio_acima_do_limite_bloqueado(app, backend_falso):
    modo_real(app)
    app.text_area(key="criterios").set_value("1. " + "x" * 2097).run()
    gerar(app)
    erro = textos(app.error)
    assert "2100" in erro and "2000" in erro
    assert backend_falso["chamadas"] == 0


# 4.2 código Mermaid copiável
def test_codigo_mermaid_disponivel(app):
    gerar(app)
    assert "stateDiagram-v2" in codigos(app)
    assert "(CA3)" in codigos(app)


# 5.1 aviso da demonstração
ABAS = 7  # grafo, análise, transições, Gherkin, Pytest, cobertura e JSON


def test_aviso_demo_em_todas_as_abas(app):
    gerar(app)
    assert sum(AVISO_DEMO in i.value for i in app.info) == ABAS


def test_modo_real_sem_aviso_demo(app, backend_falso):
    modo_real(app)
    gerar(app)
    assert not any(AVISO_DEMO in i.value for i in app.info)


def test_rotulo_da_latencia_segue_a_origem_do_resultado(app):
    gerar(app)
    app.toggle[0].set_value(False).run()
    html = " ".join(m.value for m in app.markdown)
    assert "Latência (Demo)" in html and "Latência (Real)" not in html


# 5.2 demonstração restrita
def test_demo_recusa_texto_livre(app):
    app.text_area(key="user_story").set_value("Como cliente, quero pagar um boleto.").run()
    app.text_area(key="criterios").set_value("1. Boleto vencido é recusado.").run()
    gerar(app)
    aviso = textos(app.warning)
    assert "texto livre" in aviso and "Desative" in aviso
    assert "resultado" not in app.session_state
    assert not app.get("download_button")


def test_demo_recusa_exemplo_editado(app):
    app.text_area(key="criterios").set_value(obter("login").criterios + "\n4. Novo critério.").run()
    gerar(app)
    assert "editado" in textos(app.warning)
    assert "resultado" not in app.session_state


def test_demo_recusa_exemplo_sem_referencia(monkeypatch):
    monkeypatch.setitem(demo_data.EXEMPLOS, "Boleto", {
        "sistema": None, "gabarito": None, "user_story": "Como cliente, quero pagar um boleto.",
        "criterios": "1. Boleto vencido é recusado.",
    })
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    at.selectbox(key="exemplo").select("Boleto").run()
    gerar(at)
    assert "não tem modelo de referência" in textos(at.warning)
    assert "resultado" not in at.session_state


# 4.4 gabaritos na demonstração
@pytest.mark.parametrize("nome, gabarito", [("Cupom Promocional", "cupom-promocional"),
                                            ("Autenticação MFA", "mfa-bloqueio"),
                                            ("Carrinho de Compras", "carrinho")])
def test_demo_exibe_gabarito_como_esqueleto(app, nome, gabarito):
    app.selectbox(key="exemplo").select(nome).run()
    gerar(app)
    assert not app.warning
    assert app.session_state["resultado"]["modelo"] == exemplos.carregar(gabarito)["modelo"]
    assert sum(AVISO_DEMO in i.value for i in app.info) == ABAS
    assert any("esqueletos" in i.value for i in app.info)
    assert f'scenarios("{gabarito}.feature")' in codigos(app)
    assert len(downloads(app)) == DOWNLOADS


# 4.3 análise, variáveis e tentativas
def test_aba_analise_mostra_analise_e_variaveis(app):
    app.selectbox(key="exemplo").select("Cupom Promocional").run()
    gerar(app)
    modelo = app.session_state["resultado"]["modelo"]
    assert any(modelo["analise"] in m.value for m in app.markdown)
    tabelas = [d.value for d in app.dataframe]
    variaveis = next(t for t in tabelas if "Categoria" in t.columns)
    assert list(variaveis["Nome"]) == ["data_atual", "validade", "valor_compra", "cupom_usado"]


def test_aba_analise_sem_variaveis(app):
    gerar(app)
    assert any("não declara variáveis" in c.value for c in app.caption)


def test_tentativas_do_modo_real(app, backend_falso):
    backend_falso["resposta"] = RespostaFalsa({
        "modelo": obter("login").modelo, "tentativas": 2, "duracao": 9.0,
        "historico": [{"resultado": "invalido", "duracao": 4.0, "erro": "critério 2 sem transição"},
                      {"resultado": "valido", "duracao": 5.0, "erro": ""}],
    })
    modo_real(app)
    gerar(app)
    tentativas = next(d.value for d in app.dataframe if "Tentativa" in d.value.columns)
    assert list(tentativas["Resultado"]) == ["INVÁLIDO", "VÁLIDO"]
    assert "critério 2 sem transição" in list(tentativas["Erros"])


def test_transicoes_mostram_guarda_e_acoes(app):
    app.selectbox(key="exemplo").select("Autenticação MFA").run()
    gerar(app)
    transicoes = next(d.value for d in app.dataframe if "Guarda" in d.value.columns)
    assert "tentativas < 2" in list(transicoes["Guarda"])
    assert "tentativas += 1" in list(transicoes["Ações"])


def test_demo_exibe_exemplo_nao_editado(app):
    gerar(app)
    assert not app.warning
    assert app.session_state["resultado"]["modelo"] == obter("login").modelo


# execução
def test_executar_mostra_veredito_e_nova_geracao_descarta(app):
    gerar(app)
    app.button(key="executar").click().run()
    assert not app.exception
    assert any("Bug detectado" in s.value for s in app.success)
    assert len(_tabelas_status(app)) == 2  # sistema correto e sistema com bug
    assert any("Esperado ContaBloqueada, obtido DuasFalhas" in m.value for m in app.markdown)

    gerar(app)
    assert "execucao" not in app.session_state
    assert not app.success


def test_executar_saque(app):
    app.selectbox(key="exemplo").select(SAQUE).run()
    gerar(app)
    app.button(key="executar").click().run()
    assert any("Bug detectado" in s.value for s in app.success)


# add-llm-providers 5.1: provedor e modelo na barra lateral
def test_provedores_vem_do_registro(app):
    from backend.provedores import REGISTRO

    seletor = app.selectbox(key="provedor")
    assert seletor.options == [p.nome for p in REGISTRO.values()]
    assert seletor.value == "ollama"


def test_motor_e_modelo_enviados(app, backend_falso):
    modo_real(app)
    app.selectbox(key="provedor").set_value("anthropic").run()
    app.text_input(key="modelo_llm").input("claude-sonnet-5-5").run()
    gerar(app)
    assert backend_falso["enviado"]["motor"] == "anthropic"
    assert backend_falso["enviado"]["modelo"] == "claude-sonnet-5-5"
    assert "api_key" not in backend_falso["enviado"]


def test_modelo_vazio_nao_e_enviado(app, backend_falso):
    modo_real(app)
    gerar(app)
    assert backend_falso["enviado"]["motor"] == "ollama"
    assert "modelo" not in backend_falso["enviado"]


def test_aviso_de_envio_para_a_nuvem(app):
    aviso = "requisitos digitados serão enviados"
    assert not any(aviso in c.value for c in app.caption)  # Ollama é local
    app.selectbox(key="provedor").set_value("anthropic").run()
    assert any(aviso in c.value for c in app.caption)


def test_chave_do_gemini_so_para_o_gemini(app):
    assert not [t for t in app.text_input if "Gemini" in (t.label or "")]
    app.selectbox(key="provedor").set_value("gemini").run()
    assert [t for t in app.text_input if "Gemini" in (t.label or "")]


# apply-qac-design-system: identidade visual
import ast
import json

RAIZ = Path(APP).parent
KIT = RAIZ / "assets" / "QUALITY ASSURANCE CONSULTANT" / "QUALITY ASSURANCE CONSULTANT"
MARCA = "QUALITY ASSURANCE CONSULTANT"
PROIBIDOS = ["QA Autonomous", "🤖", "🔍", "🔎", "🐛", "🐞", "🧠", "✨"]
CORES_ANTIGAS = ["#4f46e5", "#4338ca", "#0284c7", "#6366f1", "#e0e7ff", "#eef2ff"]


def _tokens_do_app() -> dict:
    arvore = ast.parse(Path(APP).read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(getattr(a, "id", None) == "TOKENS" for a in no.targets):
            return ast.literal_eval(no.value)
    raise AssertionError("TOKENS não encontrado em app.py")


def _texto_renderizado(at) -> str:
    partes = []
    for tipo in ("markdown", "caption", "info", "warning", "error", "success", "title", "header", "subheader"):
        partes += [str(e.value) for e in at.get(tipo)]
    for tipo in ("button", "download_button", "selectbox", "text_input", "text_area", "toggle", "checkbox"):
        partes += [str(e.label) for e in at.get(tipo)]
    partes += [str(e.label) for e in at.tabs] + [str(e.label) for e in at.expander]
    for d in at.dataframe:
        partes.append(d.value.to_string())
    partes.append(codigos(at))
    return "\n".join(partes)


def test_tokens_iguais_ao_kit():
    kit = json.loads((KIT / "tokens.json").read_text(encoding="utf-8"))
    claro = {t["name"]: (t["value"]["light"] if isinstance(t["value"], dict) else t["value"]).upper()
             for t in kit["color"]["tokens"]}
    tokens = _tokens_do_app()
    assert {k: v.upper() for k, v in tokens.items()} == {k: claro[k] for k in tokens}
    assert set(tokens) == set(claro)


def test_arquivos_da_marca_copiados_do_kit():
    for grupo in ("Logos", "Icones"):
        for original in (KIT / "assets" / grupo).glob("qac-*"):
            copia = RAIZ / "assets" / original.name
            assert copia.read_bytes() == original.read_bytes(), original.name


def test_tema_do_streamlit_do_kit():
    import tomllib

    tema = tomllib.loads((RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8"))["theme"]
    claro, escuro = tema["light"], tema["dark"]
    assert {k: claro[k] for k in ("primaryColor", "backgroundColor", "secondaryBackgroundColor", "textColor",
                                  "borderColor", "greenTextColor", "redTextColor")} == {
        "primaryColor": "#111111", "backgroundColor": "#FFFFFF", "secondaryBackgroundColor": "#F4F4F4",
        "textColor": "#111111", "borderColor": "#D4D4D4", "greenTextColor": "#15803D", "redTextColor": "#B42318"}
    assert {k: escuro[k] for k in ("primaryColor", "backgroundColor", "secondaryBackgroundColor", "textColor",
                                   "borderColor", "greenTextColor", "redTextColor")} == {
        "primaryColor": "#FFC72C", "backgroundColor": "#111111", "secondaryBackgroundColor": "#2B2B2B",
        "textColor": "#FFFFFF", "borderColor": "#4A4A4A", "greenTextColor": "#4ADE80", "redTextColor": "#F97066"}
    # cores de tema só nas seções de cada tema
    assert not {k for k in tema if k not in ("light", "dark", "font")}


def test_sem_cores_antigas_nem_degrade():
    fonte = Path(APP).read_text(encoding="utf-8").lower()
    assert not [c for c in CORES_ANTIGAS if c in fonte]
    assert "gradient" not in fonte


def test_nome_da_marca_no_cabecalho(app):
    html = " ".join(m.value for m in app.markdown)
    assert MARCA in html and "De requisitos a testes executáveis." in html


def test_logo_e_icone_do_kit(monkeypatch):
    import streamlit

    chamadas = []
    monkeypatch.setattr(streamlit, "logo", lambda imagem, **kw: chamadas.append((imagem, kw)))
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    (imagem, kw), = chamadas
    assert Path(imagem) == RAIZ / "assets" / "qac-logo-horizontal-claro.svg" and Path(imagem).exists()
    assert Path(kw["icon_image"]) == RAIZ / "assets" / "qac-icone-escuro.svg"


def test_titulo_da_pagina_e_icone():
    fonte = Path(APP).read_text(encoding="utf-8")
    assert "page_title=MARCA" in fonte and 'MARCA = "QUALITY ASSURANCE CONSULTANT"' in fonte
    assert "page_icon=str(FAVICON)" in fonte and '"qac-favicon-32.png"' in fonte


def test_sem_marca_provisoria_nem_icones_proibidos(app):
    telas = [_texto_renderizado(app)]
    gerar(app)
    telas.append(_texto_renderizado(app))
    app.button(key="executar").click().run()
    telas.append(_texto_renderizado(app))
    for tela in telas:
        assert not [p for p in PROIBIDOS if p in tela]


def test_hierarquia_e_rotulos_dos_botoes(app):
    assert app.button(key="gerar").label == "Gerar testes"
    assert app.button(key="gerar").proto.type == "primary"
    gerar(app)
    assert app.button(key="executar").label == "Executar testes"
    assert app.button(key="executar").proto.type == "primary"
    rotulos = [d.proto.label for d in downloads(app)]
    assert any(r.startswith("Baixar pacote (") for r in rotulos)
    assert all(d.proto.type != "primary" for d in downloads(app))


def test_abas_com_icones_material(app):
    gerar(app)
    rotulos = [t.label for t in app.tabs]
    assert len(rotulos) == ABAS and all(r.startswith(":material/") for r in rotulos)


def test_status_aprovado_e_falhou(app):
    app.selectbox(key="exemplo").select(SAQUE).run()
    gerar(app)
    app.button(key="executar").click().run()
    correto, bug = _tabelas_status(app)
    assert {r for r, _ in correto} == {"APROVADO"}
    assert "FALHOU" in {r for r, _ in bug}
    falhas = [r for r, _ in bug].count("FALHOU")
    veredito = textos(app.success)
    assert f"Bug detectado em {falhas} teste" in veredito


# add-dark-theme
import re as _re

CLASSE_STATUS = {"ok": "APROVADO", "falha": "FALHOU"}


def _tabelas_status(at) -> list[list[tuple[str, str]]]:
    """Linhas (resultado, cenário) de cada tabela HTML de status; confere que a classe bate com a palavra."""
    tabelas = []
    for m in at.markdown:
        if 'class="qac-status"' not in m.value:
            continue
        linhas = _re.findall(r'<tr><td class="(ok|falha)">(APROVADO|FALHOU)</td><td>(.*?)</td></tr>', m.value)
        assert all(CLASSE_STATUS[c] == r for c, r, _ in linhas)
        tabelas.append([(r, nome) for _, r, nome in linhas])
    return tabelas


def _bloco(nome: str):
    """Valor literal de uma atribuição de nível de módulo em app.py, sem executar o app."""
    arvore = ast.parse(Path(APP).read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(getattr(a, "id", None) == nome for a in no.targets):
            return no
    raise AssertionError(f"{nome} não encontrado em app.py")


def _css(at) -> str:
    return next(m.value for m in at.markdown if m.value.lstrip().startswith("<style>"))


def _kit_escuro() -> dict:
    kit = json.loads((KIT / "tokens.json").read_text(encoding="utf-8"))
    return {t["name"]: (t["value"]["dark"] if isinstance(t["value"], dict) else t["value"]).upper()
            for t in kit["color"]["tokens"]}


def _tokens_escuros_do_app() -> dict:
    no = _bloco("TOKENS_ESCURO").value  # {**TOKENS, ...}
    tokens = dict(_tokens_do_app())
    for chave, valor in zip(no.keys, no.values):
        if chave is not None:
            tokens[ast.literal_eval(chave)] = ast.literal_eval(valor)
    return tokens


def test_tokens_escuros_iguais_ao_kit():
    tokens = {k: v.upper() for k, v in _tokens_escuros_do_app().items()}
    assert tokens == _kit_escuro()


def test_css_com_os_dois_temas(app):
    css = _css(app)
    claro = css.split(":root {", 1)[1].split("}", 1)[0]
    escuro = css.split(':root[data-qac-tema="escuro"] {', 1)[1].split("}", 1)[0]
    for nome, valor in _tokens_do_app().items():
        assert f"--qac-{nome}: {valor};" in claro
    for nome, valor in _tokens_escuros_do_app().items():
        assert f"--qac-{nome}: {valor};" in escuro
    # fora das declarações de variável, nenhuma cor fixa
    regras = "\n".join(l for l in css.splitlines() if not l.strip().startswith("--qac-"))
    assert not _re.findall(r"#[0-9a-fA-F]{3,8}\b", regras)


def test_script_de_tema_na_pagina(app):
    scripts = [h.proto.body for h in app.get("html") if "__qacTema" in h.proto.body]
    assert len(scripts) == 1
    assert "prefers-color-scheme: dark" in scripts[0] and "MutationObserver" in scripts[0]


def test_logos_e_pato_nos_dois_temas(app):
    html = " ".join(m.value for m in app.sidebar.markdown)
    for arquivo in ("qac-logo-horizontal-claro.svg", "qac-logo-horizontal-escuro.svg"):
        assert (RAIZ / "assets" / arquivo).read_text(encoding="utf-8") in html
    assert 'class="qac-logo qac-so-claro"' in html and 'class="qac-logo qac-so-escuro"' in html
    vazio = next(m.value for m in app.main.markdown if 'class="empty"' in m.value)
    assert 'class="qac-so-claro"' in vazio and 'class="qac-so-escuro"' in vazio


def test_tabela_de_status_escapa_nomes():
    from types import SimpleNamespace

    import html as html_mod

    fonte = Path(APP).read_text(encoding="utf-8")
    funcao = next(n for n in ast.parse(fonte).body if isinstance(n, ast.FunctionDef) and n.name == "tabela_cenarios")
    escopo = {"html": html_mod, "APROVADO": "APROVADO", "FALHOU": "FALHOU", "ResultadoVariante": object}
    exec(compile(ast.Module([funcao], []), APP, "exec"), escopo)
    resultado = SimpleNamespace(cenarios=[SimpleNamespace(nome="saldo < 0 <b>", passou=False)])
    tabela = escopo["tabela_cenarios"](resultado)
    assert "saldo &lt; 0 &lt;b&gt;" in tabela and "<b>" not in tabela
    assert '<td class="falha">FALHOU</td>' in tabela


def test_mermaid_com_as_duas_paletas(monkeypatch):
    import streamlit

    capturado = []
    original = streamlit.iframe
    monkeypatch.setattr(streamlit, "iframe", lambda src, **kw: capturado.append(src) or original(src, **kw))
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    gerar(at)
    pagina = next(p for p in capturado if "mermaid" in p)
    for tokens in (_tokens_do_app(), _tokens_escuros_do_app()):
        for chave in ("bg", "surface", "text", "text-secondary"):
            assert tokens[chave] in pagina
    assert not [c for c in CORES_ANTIGAS if c in pagina.lower()]


def test_legenda_do_tema(app):
    assert any(c.value.endswith("Tema claro ou escuro: menu ⋮ no canto superior direito.") for c in app.sidebar.caption)
