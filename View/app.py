import base64
import datetime
import hashlib
import html
import json
import os
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# ============================================================
# CONFIGURAÇÃO
# ============================================================
st.set_page_config(
    page_title="Análise do punho com IA",
    page_icon=str(ASSETS_DIR / "Logo.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/predict/predictAI")
API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    api_base, separador, _ = API_URL.rpartition("/predict/predictAI")
    API_BASE_URL = api_base if separador else API_URL.rsplit("/", 1)[0]
API_BASE_URL = API_BASE_URL.rstrip("/")
REPORT_ENDPOINT = os.getenv("REPORT_ENDPOINT", "/reports/reportpdf")
REQUEST_TIMEOUT = 600
MAX_IMG = 20
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
PAGINAS_VALIDAS = frozenset(
    {
        "inicio",
        "login",
        "analise",
        "cadastrar_usuario",
        "atualizar_usuario",
        "excluir_usuario",
    }
)
CHAVE_PARAMETRO_PAGINA = "pagina"
CHAVE_PARAMETRO_MODO_ANALISE = "modo"
PERSISTIR_SESSAO_NAVEGADOR = os.getenv(
    "PERSISTIR_SESSAO_NAVEGADOR", "true"
).strip().lower() not in {"0", "false", "no", "off"}
HERO_IMAGE = ASSETS_DIR / "img_raioX_mao_completa.png"
PATIENT_ICON = base64.b64encode(
    (ASSETS_DIR / "registo-medico.png").read_bytes()
).decode("ascii")
XRAY_ICON = base64.b64encode((ASSETS_DIR / "corpo.png").read_bytes()).decode("ascii")
BROWSER_SESSION = components.declare_component(
    "browser_session",
    path=ASSETS_DIR.parent / "components" / "browser_session",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"<style>{(Path(__file__).resolve().parent / 'styles.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)


# ============================================================
# ESTADO, MENSAGENS E NAVEGAÇÃO
# ============================================================
def inicializar_estado():
    valores_iniciais = {
        "pagina": "inicio",
        "access_token": None,
        "usuario_logado": None,
        "incluir_dados_paciente": False,
    }
    for chave, valor in valores_iniciais.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def _atualizar_url_da_pagina(pagina, incluir_dados_paciente=None):
    if st.query_params.get(CHAVE_PARAMETRO_PAGINA) != pagina:
        st.query_params[CHAVE_PARAMETRO_PAGINA] = pagina

    if pagina == "analise":
        modo = "completa" if incluir_dados_paciente else "rapida"
        if st.query_params.get(CHAVE_PARAMETRO_MODO_ANALISE) != modo:
            st.query_params[CHAVE_PARAMETRO_MODO_ANALISE] = modo
    elif CHAVE_PARAMETRO_MODO_ANALISE in st.query_params:
        del st.query_params[CHAVE_PARAMETRO_MODO_ANALISE]


def sincronizar_navegacao_com_url():
    pagina_url = st.query_params.get(CHAVE_PARAMETRO_PAGINA)
    pagina_atual = (
        pagina_url if pagina_url in PAGINAS_VALIDAS else st.session_state.pagina
    )
    if pagina_atual not in PAGINAS_VALIDAS:
        pagina_atual = "inicio"

    st.session_state.pagina = pagina_atual
    if pagina_atual == "analise":
        st.session_state.incluir_dados_paciente = (
            st.query_params.get(CHAVE_PARAMETRO_MODO_ANALISE) == "completa"
        )

    _atualizar_url_da_pagina(
        pagina_atual,
        st.session_state.incluir_dados_paciente,
    )


def navegar(pagina, incluir_dados_paciente=None):
    if pagina not in PAGINAS_VALIDAS:
        raise ValueError(f"Página inválida: {pagina}")

    if incluir_dados_paciente is not None:
        st.session_state.incluir_dados_paciente = incluir_dados_paciente

    st.session_state.pagina = pagina
    _atualizar_url_da_pagina(
        pagina,
        st.session_state.incluir_dados_paciente,
    )
    st.rerun()


def definir_mensagem(tipo, texto):
    st.session_state.mensagem_pendente = (tipo, texto)


def exibir_mensagem_pendente():
    mensagem = st.session_state.pop("mensagem_pendente", None)
    if mensagem is None:
        return

    tipo, texto = mensagem
    getattr(st, tipo)(texto)


def limpar_autenticacao():
    st.session_state.access_token = None
    st.session_state.usuario_logado = None
    st.session_state.limpar_sessao_navegador = True


def redirecionar_por_sessao_expirada():
    limpar_autenticacao()
    definir_mensagem(
        "warning",
        "Faça login para continuar. Sua sessão pode ter expirado.",
    )
    navegar("login")


# ============================================================
# APOIO DE INTERFACE
# ============================================================
def renderizar_cabecalho(titulo, descricao, classe_titulo=""):
    st.markdown(
        f'<div class="page-title {classe_titulo}">{html.escape(titulo)}</div>'
        f'<div class="page-description">{html.escape(descricao)}</div>',
        unsafe_allow_html=True,
    )


def renderizar_card_inicio(
    titulo, descricao, icone, texto_alternativo, secundario=False
):
    classe = "card-shell secondary" if secundario else "card-shell"
    st.markdown(
        f"""
        <div class="{classe}">
            <div class="card-icon">
                <img src="data:image/png;base64,{icone}" alt="{html.escape(texto_alternativo)}">
            </div>
            <h3>{html.escape(titulo)}</h3>
            <p>{html.escape(descricao)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def assinatura_arquivos(arquivos):
    return tuple(
        (arquivo.name, hashlib.sha256(arquivo.getvalue()).hexdigest())
        for arquivo in arquivos
    )


def limpar_resultados_analise(prefixo):
    st.session_state[f"{prefixo}_resultados"] = None
    st.session_state[f"{prefixo}_assinatura"] = None


def limpar_selecao(prefixo):
    st.session_state[f"{prefixo}_upload_version"] = (
        st.session_state.get(f"{prefixo}_upload_version", 0) + 1
    )
    limpar_resultados_analise(prefixo)


# ============================================================
# CLIENTE HTTP E AUTENTICAÇÃO
# ============================================================
def detalhe_erro_api(response):
    try:
        payload = response.json()
    except ValueError:
        return response.text or "A API não informou detalhes do erro."
    if isinstance(payload, dict):
        detalhe = payload.get("detail", payload.get("erro"))
        if detalhe is not None:
            return str(detalhe)
    return str(payload)


def requisitar_api(
    metodo,
    endpoint,
    token=None,
    timeout=30,
    redirecionar_ao_expirar=False,
    exibir_erros=True,
    **kwargs,
):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            metodo,
            f"{API_BASE_URL}{endpoint}",
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
        response.raise_for_status()
        return response
    except requests.Timeout:
        if exibir_erros:
            st.error("A API demorou além do limite para responder.")
    except requests.ConnectionError:
        if exibir_erros:
            st.error("Não foi possível conectar à API.")
    except requests.HTTPError:
        if response.status_code == 401 and redirecionar_ao_expirar:
            redirecionar_por_sessao_expirada()
        if exibir_erros:
            st.error(f"Erro HTTP {response.status_code}: {detalhe_erro_api(response)}")
    except requests.RequestException as erro:
        if exibir_erros:
            st.error(f"Falha ao consultar a API: {erro}")
    return None


def carregar_usuario(token, exibir_erros=True):
    response = requisitar_api(
        "GET",
        "/user/me",
        token=token,
        exibir_erros=exibir_erros,
    )
    if response is None:
        return None
    try:
        usuario = response.json()
    except ValueError:
        if exibir_erros:
            st.error("A API retornou os dados do usuário em formato inválido.")
        return None
    campos_obrigatorios = {"username", "email", "nivel_acesso"}
    if not isinstance(usuario, dict) or not campos_obrigatorios.issubset(usuario):
        if exibir_erros:
            st.error("A API retornou os dados do usuário em formato inválido.")
        return None
    return usuario


def sincronizar_sessao_navegador():
    if not PERSISTIR_SESSAO_NAVEGADOR:
        return

    limpar_sessao = st.session_state.pop("limpar_sessao_navegador", False)
    token_atual = None if limpar_sessao else st.session_state.get("access_token")
    sessao_salva = BROWSER_SESSION(
        accessToken=token_atual,
        clear=limpar_sessao,
        default=None,
        key="browser_session",
    )

    if limpar_sessao or token_atual or not isinstance(sessao_salva, dict):
        return

    token_salvo = sessao_salva.get("access_token")
    if not isinstance(token_salvo, str) or not token_salvo:
        return

    usuario = carregar_usuario(token_salvo, exibir_erros=False)
    if usuario is None:
        st.session_state.limpar_sessao_navegador = True
        st.rerun()

    st.session_state.access_token = token_salvo
    st.session_state.usuario_logado = usuario


def realizar_login(email, senha):
    if not email or not senha:
        st.error("Digite o e-mail e a senha.")
        return

    response = requisitar_api(
        "POST",
        "/auth/login",
        json={"email": email, "password": senha},
    )
    if response is None:
        return

    try:
        resposta = response.json()
    except ValueError:
        st.error("A API retornou a resposta de login em formato inválido.")
        return

    token = resposta.get("access_token") if isinstance(resposta, dict) else None
    if not token:
        st.error("A API não retornou um token de acesso válido.")
        return

    usuario = carregar_usuario(token)
    if usuario is None:
        return

    st.session_state.access_token = token
    st.session_state.usuario_logado = usuario
    definir_mensagem("success", f"Bem-vindo(a), {usuario['username']}!")
    navegar("inicio")


def encerrar_sessao():
    limpar_autenticacao()
    navegar("inicio")


def buscar_usuario_por_email(email):
    response = requisitar_api(
        "GET",
        "/user/userByEmail",
        token=st.session_state.access_token,
        redirecionar_ao_expirar=True,
        params={"email": email},
    )
    if response is None:
        return None
    try:
        usuario = response.json()
    except ValueError:
        st.error("A API retornou os dados do usuário em formato inválido.")
        return None
    if not isinstance(usuario, dict):
        st.error("A API retornou os dados do usuário em formato inválido.")
        return None
    return usuario


def usuario_administrador():
    usuario = st.session_state.get("usuario_logado")
    return isinstance(usuario, dict) and usuario.get("nivel_acesso") == 1


# ============================================================
# APOIO DE USUÁRIOS
# ============================================================
def renderizar_formulario_usuario(modo, usuario=None, prefixo=None):
    usuario = usuario or {}
    prefixo = prefixo or modo
    with st.form(f"form_usuario_{prefixo}"):
        coluna1, coluna2 = st.columns(2)
        with coluna1:
            username = st.text_input(
                "Nome",
                value=usuario.get("username", ""),
                key=f"{prefixo}_username",
            )
            email = st.text_input(
                "E-mail",
                value=usuario.get("email", ""),
                key=f"{prefixo}_email",
            )
            registro = st.text_input(
                "Registro profissional",
                value=usuario.get("registro_profissional", ""),
                key=f"{prefixo}_registro",
            )
        with coluna2:
            cargo = st.text_input(
                "Cargo",
                value=usuario.get("cargo", ""),
                key=f"{prefixo}_cargo",
            )
            uf_registro = st.text_input(
                "UF do registro",
                value=usuario.get("uf_registro", ""),
                max_chars=2,
                key=f"{prefixo}_uf",
            )
            if modo == "registro":
                senha = st.text_input(
                    "Senha (mínimo de 12 caracteres)",
                    type="password",
                    key=f"{prefixo}_senha",
                )
            else:
                ativo = st.checkbox(
                    "Usuário ativo",
                    value=usuario.get("ativo", True),
                    key=f"{prefixo}_ativo",
                )

        enviar = st.form_submit_button(
            "Cadastrar usuário" if modo == "registro" else "Salvar alterações",
            width="stretch",
        )

    if not enviar:
        return None

    dados = {
        "username": username.strip(),
        "email": email.strip(),
        "registro_profissional": registro.strip(),
        "cargo": cargo.strip(),
        "uf_registro": uf_registro.strip().upper(),
    }
    if modo == "registro":
        dados["password"] = senha
    else:
        dados["ativo"] = ativo
    return dados


# ============================================================
# APOIO À ANÁLISE E AO RELATÓRIO
# ============================================================
def coletar_dados_paciente():
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        nome = st.text_input("Nome do paciente:")

        data_nascimento = st.date_input(
            label="Data de nascimento:",
            value="today",
            min_value=datetime.date(1900, 1, 1),
            max_value="today",
            format="DD/MM/YYYY",
        )

    with coluna2:
        sexo = st.selectbox(
            "Sexo:",
            ["Não informado", "Feminino", "Masculino"],
            index=None,
            placeholder="Selecionar--",
        )

        lado_analisado = st.selectbox(
            "Lado analisado:",
            ["Direito", "Esquerdo", "Ambos"],
            index=None,
            placeholder="Selecionar--",
        )

    # A idade é calculada pelo serviço de relatório a partir desta data.
    return {
        "name": nome.strip(),
        "sexo": sexo,
        "ladoAnalisado": lado_analisado,
        "dataNcmto": data_nascimento.isoformat(),
    }


def iniciar_analise(arquivos):
    if not arquivos:
        st.warning("Selecione ao menos uma radiografia antes de iniciar a análise.")
        return None
    if len(arquivos) > MAX_IMG:
        st.warning(f"Selecione no máximo {MAX_IMG} radiografias por análise.")
        return None
    if any(arquivo.size > MAX_IMAGE_SIZE_BYTES for arquivo in arquivos):
        st.warning("Cada imagem pode ter no máximo 5 MB.")
        return None

    files = [
        (
            "files",
            (
                arquivo.name,
                arquivo.getvalue(),
                arquivo.type or "application/octet-stream",
            ),
        )
        for arquivo in arquivos
    ]

    with st.spinner("Enviando e analisando as imagens..."):
        try:
            headers = {}
            if st.session_state.access_token:
                headers["Authorization"] = f"Bearer {st.session_state.access_token}"
            response = requests.post(
                API_URL,
                files=files,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            resposta = response.json()
        except requests.Timeout:
            st.error("A API demorou além do limite para responder.")
            return None
        except requests.ConnectionError:
            st.error("Não foi possível conectar à API.")
            return None
        except requests.HTTPError:
            detalhe = detalhe_erro_api(response)
            if response.status_code == 401:
                redirecionar_por_sessao_expirada()
            st.error(f"Erro HTTP {response.status_code}: {detalhe}")
            return None
        except (requests.RequestException, ValueError) as erro:
            st.error(f"Falha ao consultar a API: {erro}")
            return None

    if not isinstance(resposta, dict) or not isinstance(
        resposta.get("resultados"), list
    ):
        st.error("A API retornou uma resposta em formato inválido.")
        return None
    return resposta


def dados_paciente_validos(dados_paciente):
    campos_obrigatorios = {
        "name": "nome do paciente",
        "sexo": "sexo",
        "ladoAnalisado": "lado analisado",
        "dataNcmto": "data de nascimento",
    }
    ausentes = [
        nome
        for campo, nome in campos_obrigatorios.items()
        if not dados_paciente.get(campo)
    ]
    if ausentes:
        st.warning("Informe " + ", ".join(ausentes) + " antes de gerar o relatório.")
        return False
    return True


def gerar_relatorio_pdf(dados_paciente, resposta, token):
    payload = {
        "pacienteInfo": dados_paciente,
        "resultadosInfo": resposta,
    }
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.request(
        "GET",
        f"{API_BASE_URL}{REPORT_ENDPOINT}",
        headers=headers,
        timeout=REQUEST_TIMEOUT,
        json=payload,
    )
    response.raise_for_status()

    pdf = response.content
    if not pdf or not pdf.startswith(b"%PDF"):
        raise ValueError("A API não retornou um arquivo PDF válido.")
    return pdf


def renderizar_acao_relatorio(dados_paciente, prefixo):
    resposta = st.session_state.get(f"{prefixo}_resultados")
    if not resposta:
        return

    if not dados_paciente_validos(dados_paciente):
        return

    token = st.session_state.access_token
    st.markdown("### Relatório")
    colunas = st.columns([1, 2, 1])
    with colunas[1]:
        st.download_button(
            "Gerar e baixar relatório PDF",
            # Deferred generation lets the native download button return the PDF on this click.
            data=lambda: gerar_relatorio_pdf(
                dados_paciente,
                resposta,
                token,
            ),
            file_name="relatorio.pdf",
            mime="application/pdf",
            key=f"{prefixo}_gerar_pdf",
            on_click="ignore",
            width="stretch",
        )


def renderizar_resultados(arquivos, prefixo):
    resposta = st.session_state.get(f"{prefixo}_resultados")
    assinatura = st.session_state.get(f"{prefixo}_assinatura")
    if resposta is None:
        return False

    if assinatura != assinatura_arquivos(arquivos):
        st.info(
            "A seleção foi alterada. Envie as imagens novamente para atualizar os resultados."
        )
        return False

    resultados = resposta.get("resultados", [])
    sucessos = resposta.get("sucessos", 0)
    erros = resposta.get("erros", 0)
    resumo = f"{sucessos} imagem(ns) analisada(s), {erros} com erro."
    if erros and not sucessos:
        st.error(resumo)
    elif erros:
        st.warning(resumo)
    else:
        st.success(resumo)

    st.markdown("### Resultados das análises")
    for indice, arquivo in enumerate(arquivos):
        resultado = resultados[indice] if indice < len(resultados) else None
        with st.expander(f"{indice + 1}. {arquivo.name}", expanded=False):
            coluna_imagem, coluna_resultado = st.columns([1.2, 1])

            with coluna_imagem:
                imagem_final = resultado.get("final_img") if resultado else None
                if imagem_final:
                    st.image(
                        base64.b64decode(imagem_final),
                        caption="Radiografia com as detecções do modelo",
                        width="stretch",
                    )
                else:
                    st.image(
                        arquivo.getvalue(),
                        caption="Radiografia enviada",
                        width="stretch",
                    )

            with coluna_resultado:
                if resultado is None:
                    st.error("A API não retornou um resultado para esta imagem.")
                    continue

                if not isinstance(resultado, dict):
                    st.error("A API retornou um resultado inválido para esta imagem.")
                    continue

                if not resultado.get("sucesso", False):
                    detalhe = resultado.get(
                        "erro", "Não foi possível analisar esta imagem."
                    )
                    status_code = resultado.get("status_code")
                    st.error(
                        f"HTTP {status_code}: {detalhe}" if status_code else detalhe
                    )
                    continue

                deteccoes = resultado.get("detections", [])
                total_fraturas = resultado.get("total_fraturas", len(deteccoes))
                if total_fraturas:
                    st.error(resultado.get("predict", "Indicação de fratura detectada"))
                else:
                    st.success(resultado.get("predict", "Sem indicação de fratura"))

                st.write(f"**Quantidade de fraturas:** {total_fraturas}")
                if deteccoes:
                    st.write("**Confiança da predição:**")
                    for numero, deteccao in enumerate(deteccoes, start=1):
                        confianca = deteccao.get("confidence")
                        if confianca is not None:
                            st.write(f"Fratura {numero}: {float(confianca):.1%}")

    if len(resultados) > len(arquivos):
        st.warning("A API retornou resultados adicionais sem imagem correspondente.")

    return True


# ============================================================
# TELAS
# ============================================================
def renderizar_tela_inicio():
    hero_texto, hero_imagem = st.columns(
        [1.2, 1], gap="large", vertical_alignment="center"
    )

    with hero_texto:
        st.markdown(
            """
            <div class="hero-shell">
                <h1 class="hero-title">
                    Análise de fraturas<br>
                    <span>no punho</span> com IA
                </h1>
                <p class="hero-description">
                    Um sistema de apoio que utiliza inteligência artificial
                    para auxiliar na análise de radiografias do punho.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with hero_imagem:
        with st.container(key="home_hero_image"):
            st.image(HERO_IMAGE, width="stretch")

    coluna_completa, coluna_rapida = st.columns(2, gap="large")
    with coluna_completa:
        renderizar_card_inicio(
            "Nova análise com dados do paciente",
            "Informe os dados do paciente e gere um relatório com o resultado.",
            PATIENT_ICON,
            "Registro médico",
        )
        if st.button("Nova Análise →", key="nova_analise", width="stretch"):
            limpar_selecao("analise")
            navegar("analise", incluir_dados_paciente=True)

    with coluna_rapida:
        renderizar_card_inicio(
            "Análise rápida",
            "Envie uma radiografia do punho e obtenha o resultado rapidamente, sem informar os dados do paciente.",
            XRAY_ICON,
            "Radiografia",
            secundario=True,
        )
        if st.button(
            "Nova Análise Rápida →",
            key="analise_rapida",
            width="stretch",
        ):
            limpar_selecao("analise")
            navegar("analise", incluir_dados_paciente=False)

    st.markdown(
        """
        <div class="disclaimer">
            Este sistema é apenas um apoio à análise radiológica e não substitui a avaliação de um profissional médico.
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_tela_analise():
    incluir_dados_paciente = st.session_state.incluir_dados_paciente
    titulo = "Análise Completa" if incluir_dados_paciente else "Análise rápida"
    descricao = (
        "Informe os dados do paciente e envie até 20 radiografias para análise."
        if incluir_dados_paciente
        else "Envie até 20 radiografias para análise."
    )
    renderizar_cabecalho(titulo, descricao, "analysis-page-title")

    dados_paciente = coletar_dados_paciente() if incluir_dados_paciente else None
    prefixo = "analise"
    versao_upload = st.session_state.get(f"{prefixo}_upload_version", 0)
    arquivos = st.file_uploader(
        "Selecione até 20 radiografias",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"{prefixo}_upload_{versao_upload}",
    )

    if arquivos:
        st.caption(f"{len(arquivos)} imagens selecionadas")
        colunas = st.columns(6)
        for indice, arquivo in enumerate(arquivos):
            with colunas[indice % 6]:
                st.image(arquivo.getvalue(), caption=arquivo.name, width=100)

    st.button(
        "Limpar seleção",
        key="limpar_analise",
        on_click=limpar_selecao,
        args=(prefixo,),
    )

    if st.button("Iniciar análises", key="enviar_analise", width="stretch"):
        limpar_resultados_analise(prefixo)
        resposta = iniciar_analise(arquivos)
        if resposta is not None:
            st.session_state[f"{prefixo}_resultados"] = resposta
            st.session_state[f"{prefixo}_assinatura"] = assinatura_arquivos(arquivos)
            st.rerun()

    resultados_atuais = renderizar_resultados(arquivos or [], prefixo)
    if incluir_dados_paciente and resultados_atuais:
        renderizar_acao_relatorio(dados_paciente, prefixo)

    st.divider()
    if st.button("← Voltar ao início", key="voltar_analise"):
        navegar("inicio")


def renderizar_tela_login():
    renderizar_cabecalho("Login", "Acesso ao sistema.")
    with st.container(border=True):
        with st.form("login_form"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", width="stretch")

    if entrar:
        realizar_login(email, senha)
    st.divider()
    if st.button("← Voltar", key="voltar_login"):
        navegar("inicio")


def renderizar_tela_cadastro_usuario():
    if not usuario_administrador():
        st.error("Somente administradores podem cadastrar usuários.")
        return

    renderizar_cabecalho(
        "Cadastrar usuário",
        "Preencha os dados para criar uma nova conta de acesso.",
    )
    dados = renderizar_formulario_usuario("registro")
    if dados is None:
        return

    response = requisitar_api(
        "POST",
        "/user/userRegister",
        token=st.session_state.access_token,
        redirecionar_ao_expirar=True,
        json=dados,
    )
    if response is not None:
        st.success("Usuário cadastrado com sucesso.")


def renderizar_tela_atualizar_usuario():
    if not usuario_administrador():
        st.error("Somente administradores podem alterar usuários.")
        return

    renderizar_cabecalho(
        "Alterar usuário",
        "Busque a conta que deseja alterar pelo e-mail.",
    )
    with st.form("buscar_usuario_atualizacao"):
        email_busca = st.text_input("E-mail do usuário")
        buscar = st.form_submit_button("Buscar usuário", width="stretch")

    if buscar:
        usuario = buscar_usuario_por_email(email_busca.strip())
        if usuario is not None:
            st.session_state.usuario_em_edicao = usuario

    usuario = st.session_state.get("usuario_em_edicao")
    if not isinstance(usuario, dict):
        return

    st.info(f"Editando: {usuario.get('username')} ({usuario.get('email')})")
    chave = hashlib.sha256(usuario["email"].encode("utf-8")).hexdigest()[:12]
    dados = renderizar_formulario_usuario(
        "atualizacao",
        usuario=usuario,
        prefixo=f"usuario_edicao_{chave}",
    )
    if dados is None:
        return

    response = requisitar_api(
        "PUT",
        "/user/userUpdate_email",
        token=st.session_state.access_token,
        redirecionar_ao_expirar=True,
        params={"email": usuario["email"]},
        json=dados,
    )
    if response is not None:
        st.session_state.pop("usuario_em_edicao", None)
        definir_mensagem("success", "Usuário atualizado com sucesso.")
        st.rerun()


def renderizar_tela_excluir_usuario():
    if not usuario_administrador():
        st.error("Somente administradores podem excluir usuários.")
        return

    renderizar_cabecalho(
        "Excluir usuário",
        "Busque a conta que deseja excluir pelo e-mail.",
    )
    with st.form("buscar_usuario_exclusao"):
        email_busca = st.text_input("E-mail do usuário")
        buscar = st.form_submit_button("Buscar usuário", width="stretch")

    if buscar:
        usuario = buscar_usuario_por_email(email_busca.strip())
        if usuario is not None:
            st.session_state.usuario_para_excluir = usuario

    usuario = st.session_state.get("usuario_para_excluir")
    if not isinstance(usuario, dict):
        return

    st.warning(
        f"Conta selecionada: {usuario.get('username')} ({usuario.get('email')}). "
        "Esta ação não pode ser desfeita."
    )
    chave = hashlib.sha256(usuario["email"].encode("utf-8")).hexdigest()[:12]
    with st.form(f"confirmar_exclusao_{chave}"):
        confirmar = st.checkbox(
            "Confirmo a exclusão desta conta.",
            key=f"confirmar_exclusao_{chave}",
        )
        excluir = st.form_submit_button("Excluir usuário", width="stretch")

    if not excluir:
        return
    if not confirmar:
        st.error("Marque a confirmação antes de excluir o usuário.")
        return

    response = requisitar_api(
        "DELETE",
        "/user/userDelete_email",
        token=st.session_state.access_token,
        redirecionar_ao_expirar=True,
        params={"email": usuario["email"]},
    )
    if response is not None:
        st.session_state.pop("usuario_para_excluir", None)
        definir_mensagem("success", "Usuário excluído com sucesso.")
        if usuario["email"] == st.session_state.usuario_logado.get("email"):
            encerrar_sessao()
        st.rerun()


def renderizar_menu_lateral():
    with st.sidebar:
        coluna_logo, coluna_titulo = st.columns([1, 2], vertical_alignment="center")
        with coluna_logo:
            st.image(
                ASSETS_DIR / "Logo_sem_fundo.png",
                width=75,
                alt="Logo do sistema",
            )
        with coluna_titulo:
            st.title("Menu")
        if st.session_state.pagina != "inicio":
            if st.button("Início", key="menu_inicio", width="stretch"):
                navegar("inicio")

        if st.button("Nova Análise", key="menu_nova_analise", width="stretch"):
            limpar_selecao("analise")
            navegar("analise", incluir_dados_paciente=True)
        if st.button(
            "Nova Análise Rápida",
            key="menu_analise_rapida",
            width="stretch",
        ):
            limpar_selecao("analise")
            navegar("analise", incluir_dados_paciente=False)

        usuario_logado = st.session_state.get("usuario_logado")
        if isinstance(usuario_logado, dict):
            coluna_icone, coluna_usuario = st.columns(
                [1, 5],
                vertical_alignment="center",
            )
            with coluna_icone:
                st.image(ASSETS_DIR / "medico.png", width=28, alt="Usuário")
            with coluna_usuario:
                with st.expander(usuario_logado["username"]):
                    st.caption(usuario_logado["email"])
                    if st.button("Sair da conta", key="menu_sair", width="stretch"):
                        encerrar_sessao()
            if usuario_administrador():
                st.divider()
                st.caption("Administração")
                if st.button(
                    "Cadastrar usuário",
                    key="menu_cadastrar_usuario",
                    width="stretch",
                ):
                    navegar("cadastrar_usuario")
                if st.button(
                    "Alterar usuário",
                    key="menu_atualizar_usuario",
                    width="stretch",
                ):
                    st.session_state.pop("usuario_em_edicao", None)
                    navegar("atualizar_usuario")
                if st.button(
                    "Excluir usuário",
                    key="menu_excluir_usuario",
                    width="stretch",
                ):
                    st.session_state.pop("usuario_para_excluir", None)
                    navegar("excluir_usuario")
        else:
            if st.button("➔ Entrar", key="menu_entrar", width="stretch"):
                navegar("login")


# ============================================================
# INICIALIZAÇÃO E ROTEAMENTO
# ============================================================
inicializar_estado()
sincronizar_navegacao_com_url()
sincronizar_sessao_navegador()
renderizar_menu_lateral()
exibir_mensagem_pendente()

TELAS = {
    "inicio": renderizar_tela_inicio,
    "login": renderizar_tela_login,
    "analise": renderizar_tela_analise,
    "cadastrar_usuario": renderizar_tela_cadastro_usuario,
    "atualizar_usuario": renderizar_tela_atualizar_usuario,
    "excluir_usuario": renderizar_tela_excluir_usuario,
}
TELAS[st.session_state.pagina]()
