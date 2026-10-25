import datetime

import streamlit as st
import requests
import base64
import hashlib
import html
import os
from pathlib import Path

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
REQUEST_TIMEOUT = 600
MAX_IMG = 20
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
HERO_IMAGE = ASSETS_DIR / "img_raioX_mao_completa.png"
PATIENT_ICON = base64.b64encode(
    (ASSETS_DIR / "registo-medico.png").read_bytes()
).decode("ascii")
XRAY_ICON = base64.b64encode((ASSETS_DIR / "corpo.png").read_bytes()).decode("ascii")


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Lato', Arial, sans-serif;
        }

        [data-testid="stHeader"] {
            background: linear-gradient(135deg, #247fb5 0%, #1760d4 100%);
        }

        [data-testid="stHeader"] button,
        [data-testid="stHeader"] button svg {
            color: #ffffff;
            fill: #ffffff;
        }

        html[data-theme="dark"] [data-testid="stHeader"] {
            background: linear-gradient(135deg, #16477d 0%, #0c2f5f 100%);
        }

        .stApp {
            background: var(--background-color);
        }

        .block-container {
            max-width: 1220px !important;
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
        }

        .hero-shell {
            padding: 1rem 0 2rem 0;
        }

        .st-key-home_hero_image {
            display: flex;
            justify-content: flex-end;
            width: calc(100% + max(0px, 50vw - 610px) + 1.5rem);
            margin-right: calc(0px - max(0px, 50vw - 610px) - 1.5rem);
        }

        @media (max-width: 768px) {
            .st-key-home_hero_image {
                width: 100%;
                margin-right: 0;
            }
        }

        .eyebrow {
            color: #247fd5;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .hero-title {
            color: var(--text-color);
            font-size: clamp(2.5rem, 5.2vw, 4.3rem);
            line-height: 0.95;
            font-weight: 800;
            letter-spacing: -2px;
            margin: 0;
            max-width: 760px;
        }

        .hero-title span {
            color: #247fd5;
        }

        .hero-description {
            color: var(--text-color);
            opacity: 0.75;
            font-size: 1.1rem;
            line-height: 1.6;
            max-width: 700px;
            margin-top: 1.2rem;
            margin-bottom: 0;
        }

        .card-shell {
            min-height: 250px;
            padding: 1.6rem 1.4rem;
            border-radius: 18px;
            border: 1px solid rgba(127, 127, 127, 0.25);
            background: var(--secondary-background-color);
            box-shadow: 0 10px 24px rgba(20, 35, 61, 0.04);
        }

        .card-shell.secondary {
            background: var(--background-color);
        }

        .card-icon {
            width: 3rem;
            height: 3rem;
            margin-bottom: 0.7rem;
        }

        .card-icon img {
            display: block;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .card-shell h3 {
            color: var(--text-color);
            font-size: 1.6rem;
            font-weight: 800;
            line-height: 1.2;
            margin: 0 0 0.7rem 0;
        }

        .card-shell p {
            color: var(--text-color);
            opacity: 0.75;
            font-size: 1rem;
            line-height: 1.55;
            margin: 0;
        }

        .disclaimer {
            margin-top: 2.8rem;
            padding-top: 1.8rem;
            border-top: 1px solid rgba(127, 127, 127, 0.25);
            color: var(--text-color);
            opacity: 0.75;
            font-size: 0.92rem;
            text-align: center;
        }

        .page-title {
            color: var(--text-color);
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 0.5rem;
        }

        .analysis-page-title {
            padding-top: 1.5rem;
        }

        .page-description {
            color: var(--text-color);
            opacity: 0.75;
            font-size: 1.05rem;
            line-height: 1.5;
            margin-bottom: 1.5rem;
        }

        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            min-height: 48px;
            font-family: 'Lato', Arial, sans-serif;
            font-size: 1rem;
            font-weight: 700;
            border: 1px solid #247fd5;
            color: #ffffff;
            background: linear-gradient(135deg, #247fb5 0%, #1760d4 100%);
            margin-top: 0.9rem;
        }

        div.stButton > button:hover {
            border-color: #1760d4;
            color: #ffffff;
            box-shadow: 0 10px 24px rgba(36, 127, 213, 0.18);
        }

        div.st-key-limpar_analise button {
            width: auto;
            min-height: 36px;
            padding: 0.35rem 0.8rem;
            color: var(--text-color);
            background: var(--secondary-background-color);
            border-color: rgba(127, 127, 127, 0.35);
            font-size: 0.9rem;
            box-shadow: none;
        }

        div.st-key-limpar_analise button:hover {
            color: #ffffff;
            background: #c62828;
            border-color: #c62828;
            box-shadow: 0 4px 12px rgba(198, 40, 40, 0.2);
        }


        html[data-theme="dark"] div.stButton > button {
            border-color: #16477d;
            background: linear-gradient(135deg, #16477d 0%, #0c2f5f 100%);
        }

        html[data-theme="dark"] div.stButton > button:hover {
            border-color: #0c2f5f;
            background: linear-gradient(135deg, #16477d 0%, #0c2f5f 100%);
            box-shadow: 0 10px 24px rgba(12, 47, 95, 0.3);
        }

        [data-testid="stFileUploader"] {
            border-radius: 12px;
            border: 1px solid rgba(127, 127, 127, 0.25);
            background: var(--secondary-background-color);
        }

        .analysis-grid {
            display: grid;
            gap: 1.1rem;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            margin-top: 1rem;
        }

        .analysis-actions {
            margin-top: 1.2rem;
            display: flex;
            gap: 0.8rem;
            align-items: center;
        }

        .analysis-actions > div {
            flex: 1;
        }

        .preview-box {
            background: var(--secondary-background-color);
            border: 1px solid rgba(127, 127, 127, 0.25);
            border-radius: 16px;
            padding: 1rem;
            margin-top: 0.8rem;
        }

        .result-box {
            background: var(--secondary-background-color);
            border: 1px solid rgba(127, 127, 127, 0.25);
            border-radius: 14px;
            padding: 25px;
            margin-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ESTADO DA APLICAÇÃO
# ============================================================

if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None


# ============================================================
# FUNÇÕES
# ============================================================
def cadastrarPaciente():
    col1, col2 = st.columns(2)

    with col1:
        nome = st.text_input("Nome do paciente:")
        sexo = st.selectbox(
            "Sexo:",
            ["Não informado", "Feminino", "Masculino"],
            index=None,
            placeholder="Selecionar--",
        )
        data_ncmto = st.date_input(
            label="Data de nascimento:",
            value="today",
            min_value=datetime.date(1900, 1, 1),
            max_value="today",
            format="DD/MM/YYYY",
        )

    with col2:
        idade = st.number_input("Idade:", min_value=0, max_value=120, value=0)
        lado = st.selectbox(
            "Lado analisado:",
            ["Direito", "Esquerdo", "Ambos"],
            index=None,
            placeholder="Selecionar--",
        )

    return nome, idade, sexo, lado, data_ncmto


def navegar(pagina):
    st.session_state.pagina = pagina
    st.rerun()


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


def Assinatura_arquivos(arquivos):
    return tuple(
        (arquivo.name, hashlib.sha256(arquivo.getvalue()).hexdigest())
        for arquivo in arquivos
    )


def Limpar_selecao(prefixo):
    st.session_state[f"{prefixo}_upload_version"] = (
        st.session_state.get(f"{prefixo}_upload_version", 0) + 1
    )
    st.session_state[f"{prefixo}_resultados"] = None
    st.session_state[f"{prefixo}_assinatura"] = None


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


def requisitar_api(metodo, endpoint, token=None, timeout=30, **kwargs):
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
        st.error("A API demorou além do limite para responder.")
    except requests.ConnectionError:
        st.error("Não foi possível conectar à API.")
    except requests.HTTPError:
        st.error(f"Erro HTTP {response.status_code}: {detalhe_erro_api(response)}")
    except requests.RequestException as erro:
        st.error(f"Falha ao consultar a API: {erro}")
    return None


def carregar_usuario(token):
    response = requisitar_api("GET", "/user/me", token=token)
    if response is None:
        return None
    try:
        usuario = response.json()
    except ValueError:
        st.error("A API retornou os dados do usuário em formato inválido.")
        return None
    campos_obrigatorios = {"username", "email", "nivel_acesso"}
    if not isinstance(usuario, dict) or not campos_obrigatorios.issubset(usuario):
        st.error("A API retornou os dados do usuário em formato inválido.")
        return None
    return usuario


def realizarLogin(email, senha):
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
    st.session_state.login_required = False
    st.session_state.pagina = "inicio"
    st.success(f"Bem-vindo(a), {usuario['username']}!")
    st.rerun()


def encerrar_sessao():
    st.session_state.access_token = None
    st.session_state.usuario_logado = None
    st.session_state.pagina = "inicio"
    st.rerun()


def buscar_usuario_por_email(email):
    response = requisitar_api(
        "GET",
        "/user/userByEmail",
        token=st.session_state.access_token,
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
#                       TELA DE CADASTRO DE USUARIO
# ============================================================
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
        json=dados,
    )
    if response is not None:
        st.success("Usuário cadastrado com sucesso.")


# ============================================================
#                       TELA DE ATUALIZACAO DE USUARIO
# ============================================================
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

    email_original = usuario["email"]
    response = requisitar_api(
        "PUT",
        "/user/userUpdate_email",
        token=st.session_state.access_token,
        params={"email": email_original},
        json=dados,
    )
    if response is not None:
        st.session_state.pop("usuario_em_edicao", None)
        st.success("Usuário atualizado com sucesso.")
        st.rerun()


# ============================================================
#                       TELA DE EXCLUSAO DE USUARIO
# ============================================================
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

    email_excluido = usuario["email"]
    response = requisitar_api(
        "DELETE",
        "/user/userDelete_email",
        token=st.session_state.access_token,
        params={"email": email_excluido},
    )
    if response is not None:
        st.session_state.pop("usuario_para_excluir", None)
        if email_excluido == st.session_state.usuario_logado.get("email"):
            encerrar_sessao()
        st.success("Usuário excluído com sucesso.")
        st.rerun()


def Iniciar_analise(arquivos):
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
                st.session_state.access_token = None
                st.session_state.usuario_logado = None
                st.session_state.login_required = True
                st.session_state.pagina = "login"
                st.rerun()
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


def renderizar_resultados(arquivos, prefixo):
    resposta = st.session_state.get(f"{prefixo}_resultados")
    assinatura = st.session_state.get(f"{prefixo}_assinatura")
    if resposta is None:
        return

    if assinatura != Assinatura_arquivos(arquivos):
        st.info(
            "A seleção foi alterada. Envie as imagens novamente para atualizar os resultados."
        )
        return

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
                imagem_processada = (
                    resultado.get("imagem_processada") if resultado else None
                )
                if imagem_processada:
                    st.image(
                        base64.b64decode(imagem_processada),
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

                deteccoes = resultado.get("detecções", [])
                total_fraturas = resultado.get("total_fraturas", len(deteccoes))
                if total_fraturas:
                    st.error(
                        resultado.get("predicao", "Indicação de fratura detectada")
                    )
                else:
                    st.success(resultado.get("predicao", "Sem indicação de fratura"))

                st.write(f"**Quantidade de fraturas:** {total_fraturas}")
                if deteccoes:
                    st.write("**Confiança da predição:**")
                    for numero, deteccao in enumerate(deteccoes, start=1):
                        confianca = deteccao.get("confidence")
                        if confianca is not None:
                            st.write(f"Fratura {numero}: {float(confianca):.1%}")

    if len(resultados) > len(arquivos):
        st.warning("A API retornou resultados adicionais sem imagem correspondente.")


# ============================================================
# NAVEGAÇÃO
# ============================================================

with st.sidebar:
    st.title("Menu")

    if st.session_state.pagina != "inicio":
        if st.button("Início", key="menu_inicio", width="stretch"):
            navegar("inicio")

    if st.button("Nova Análise", key="menu_nova_analise", width="stretch"):
        st.session_state.incluir_dados_paciente = True
        Limpar_selecao("analise")
        navegar("analise")

    if st.button("Nova Análise Rápida", key="menu_anliserapida", width="stretch"):
        st.session_state.incluir_dados_paciente = False
        Limpar_selecao("analise")
        navegar("analise")

    usuario_logado = st.session_state.get("usuario_logado")
    if isinstance(usuario_logado, dict):
        with st.expander(f"👤 {usuario_logado['username']}"):
            st.caption(usuario_logado["email"])
            st.button(
                "Sair da conta",
                key="menu_sair",
                width="stretch",
                on_click=encerrar_sessao,
            )
        if usuario_administrador():
            st.divider()
            st.caption("Administração")
            if st.button(
                "Cadastrar usuário", key="menu_cadastrar_usuario", width="stretch"
            ):
                navegar("cadastrar_usuario")
            if st.button(
                "Alterar usuário", key="menu_atualizar_usuario", width="stretch"
            ):
                st.session_state.pop("usuario_em_edicao", None)
                navegar("atualizar_usuario")
            if st.button(
                "Excluir usuário", key="menu_excluir_usuario", width="stretch"
            ):
                st.session_state.pop("usuario_para_excluir", None)
                navegar("excluir_usuario")
    elif st.button("👤 Entrar", key="menu_entrar", width="stretch"):
        navegar("login")


# ============================================================
# PÁGINA INICIAL
# ============================================================
def rederizarTelaInicial():
    if st.session_state.pagina == "inicio":

        hero_text, hero_image = st.columns(
            [1.2, 1], gap="large", vertical_alignment="center"
        )

        with hero_text:
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

        with hero_image:
            with st.container(key="home_hero_image"):
                st.image(HERO_IMAGE, width="stretch")

        col1, col2 = st.columns(2, gap="large")

        with col1:
            renderizar_card_inicio(
                "Nova análise com dados do paciente",
                "Informe os dados do paciente e gere um relatório com o resultado.",
                PATIENT_ICON,
                "Registo Médico",
            )

            if st.button(
                "Nova Análise →",
                key="nova_analise",
                width="stretch",
            ):
                st.session_state.incluir_dados_paciente = True
                Limpar_selecao("analise")
                st.session_state.pagina = "analise"
                st.rerun()

        with col2:
            renderizar_card_inicio(
                "Análise rápida",
                "Envie uma radiografia do punho e obtenha o resultado rapidamente, sem informar os dados do paciente.",
                XRAY_ICON,
                "Corpo",
                secundario=True,
            )

            if st.button(
                "Nova Análise Rápida →",
                key="analise_rapida",
                width="stretch",
            ):
                st.session_state.incluir_dados_paciente = False
                Limpar_selecao("analise")
                navegar("analise")

        st.markdown(
            """
            <div class="disclaimer">
                Este sistema é apenas um apoio à análise radiológica e não substitui a avaliação de um profissional médico.
            </div>
            """,
            unsafe_allow_html=True,
        )


rederizarTelaInicial()


# ============================================================
#                       TELA DE ANÁLISE
# ============================================================
def renderizarTelaDeAnalise():
    incluir_dados_paciente = st.session_state.get("incluir_dados_paciente", False)
    titulo = "Análise Completa" if incluir_dados_paciente else "Análise rápida"
    descricao = (
        "Informe os dados do paciente e envie até 20 radiografias para análise."
        if incluir_dados_paciente
        else "Envie até 20 radiografias para análise."
    )

    renderizar_cabecalho(titulo, descricao, "analysis-page-title")

    if incluir_dados_paciente:
        cadastrarPaciente()

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
        for i, file in enumerate(arquivos):
            with colunas[i % 6]:
                st.image(file.getvalue(), caption=file.name, width=100)

    st.button(
        "Limpar seleção",
        key="limpar_analise",
        on_click=Limpar_selecao,
        args=(prefixo,),
    )

    if st.button(
        "Iniciar análises",
        key="enviar_analise",
        width="stretch",
    ):
        st.session_state[f"{prefixo}_resultados"] = None
        st.session_state[f"{prefixo}_assinatura"] = None
        resposta = Iniciar_analise(arquivos)
        if resposta is not None:
            st.session_state[f"{prefixo}_resultados"] = resposta
            st.session_state[f"{prefixo}_assinatura"] = Assinatura_arquivos(arquivos)
            st.rerun()

    renderizar_resultados(arquivos or [], prefixo)

    if st.button("← Voltar ao início", key="voltar_analise"):
        navegar("inicio")


if st.session_state.pagina == "analise":
    renderizarTelaDeAnalise()

elif st.session_state.pagina == "login":
    renderizar_cabecalho("Login", "Acesso ao sistema.")
    if st.session_state.pop("login_required", False):
        st.warning("Faça login para continuar. Sua sessão pode ter expirado.")

    with st.container(border=True):
        with st.form("login_form"):
            usuario = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")

            entrar = st.form_submit_button(
                "Entrar",
                width="stretch",
            )

            if entrar:
                realizarLogin(usuario, senha)

    if st.button("← Voltar", key="voltar_login"):
        navegar("inicio")

# ============================================================
#                       TELA DE CADASTRO DE USUARIO
# ============================================================
elif st.session_state.pagina == "cadastrar_usuario":
    renderizar_tela_cadastro_usuario()

# ============================================================
#                       TELA DE ATUALIZACAO DE USUARIO
# ============================================================
elif st.session_state.pagina == "atualizar_usuario":
    renderizar_tela_atualizar_usuario()

# ============================================================
#                       TELA DE EXCLUSAO DE USUARIO
# ============================================================
elif st.session_state.pagina == "excluir_usuario":
    renderizar_tela_excluir_usuario()
