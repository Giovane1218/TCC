import requests
import streamlit as st
import io
import base64
import os
from PIL import Image
from utils.pdf_utils import gerar_pdf

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/predictAI/multiple")
REQUEST_TIMEOUT = 120
MAX_IMAGENS = 20

st.session_state.setdefault("uploader_key", 0)
st.session_state.setdefault("resposta", None)
st.session_state.setdefault("pdf", None)

def imagem_para_exibicao(arquivo):
    imagem = Image.open(io.BytesIO(arquivo.getvalue()))
    if imagem.mode == "P" and "transparency" in imagem.info:
        imagem = imagem.convert("RGBA")
    return imagem.convert("RGB")


def imagem_processada_para_exibicao(conteudo):
    imagem = Image.open(io.BytesIO(conteudo))
    if imagem.mode == "P" and "transparency" in imagem.info:
        imagem = imagem.convert("RGBA")
    return imagem.convert("RGB")

def limpar_selecao():
    st.session_state["uploader_key"] += 1
    st.session_state["resposta"] = None
    st.session_state["pdf"] = None

st.set_page_config(page_title="Análise de radiografias do punho", layout="wide")
st.title("🦴 Análise de radiografias do punho")
st.markdown('<div id="topo"></div>', unsafe_allow_html=True)
st.caption("Sistema de apoio à detecção de fraturas do punho usando inteligência artificial")
st.markdown("---")

st.subheader("📤 Enviar radiografias")
st.caption("Selecione de 1 até 20 radiografias para análise")

uploaded_files = st.file_uploader(
    "Selecione as radiografias:",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key=f"arquivos_raiox_{st.session_state['uploader_key']}",
)

if uploaded_files:
    if st.button("🗑️ Limpar seleção"):
        limpar_selecao()
        st.rerun()

    if len(uploaded_files) > MAX_IMAGENS:
        st.error(f"Selecione no máximo {MAX_IMAGENS} imagens por envio.")
        st.stop()

    st.info(f"📁 {len(uploaded_files)} radiografia(s) selecionada(s).")

    colunas = st.columns(5)
    for indice, arquivo in enumerate(uploaded_files):
        with colunas[indice % 5]:
            st.image(
                imagem_para_exibicao(arquivo),
                caption=arquivo.name,
                width=100,
            )
    st.caption(f" *Confira a(s) radiografia(s) acima e clique em 'Analisar' para continuar.")

    if st.button("🔍 Analisar", type="primary", use_container_width=True):
        files = [
            (
                "files",
                (
                    arquivo.name,
                    arquivo.getvalue(),
                    arquivo.type or "application/octet-stream",
                ),
            )
            for arquivo in uploaded_files
        ]

        with st.spinner("Enviando e analisando as imagens..."):
            try:
                response = requests.post(
                    API_URL,
                    files=files,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                resposta = response.json()
            except requests.Timeout:
                st.error("A API demorou além do limite para responder.")
                st.stop()
            except requests.ConnectionError:
                st.error("Não foi possível conectar à API.")
                st.stop()
            except requests.HTTPError:
                try:
                    detalhe = response.json().get("detail", response.text)
                except ValueError:
                    detalhe = response.text
                st.error(f"Erro HTTP {response.status_code}: {detalhe}")
                st.stop()
            except (requests.RequestException, ValueError) as erro:
                st.error(f"Falha ao consultar a API: {erro}")
                st.stop()

        st.session_state["resposta"] = resposta
        st.session_state["pdf"] = None  # Limpa o PDF anterior, se houver
        st.rerun()

resposta = st.session_state.get("resposta")

if resposta:
    st.success(
        f"Analise concluída com exito!"
        )
    
    st.markdown("---")
    st.subheader("Resultados da análise:")

    arquivos_por_indice = {
        indice: arquivo
        for indice, arquivo in enumerate(uploaded_files or [])
    }

    for resultado in resposta.get("resultados", []):
        nome = resultado.get("nome_arquivo", "Imagem")
        arquivo = arquivos_por_indice.get(resultado.get("indice"))

        with st.expander(nome, expanded=True):
            col_original, col_processada = st.columns(2)

            with col_original:
                st.markdown("#### Original")
                if arquivo is not None:
                    st.image(imagem_para_exibicao(arquivo), width=400)

            with col_processada:
                st.markdown("#### Resultado")

                if resultado.get("status") != "success":
                    st.error(resultado.get("erro", "Erro desconhecido"))
                    continue

                imagem_processada = resultado.get("imagem_processada")
                if imagem_processada:
                    st.image(
                        imagem_processada_para_exibicao(
                            base64.b64decode(imagem_processada)
                        ),
                        width=400,
                    )

                predicao = resultado.get("predicao", "Resultado indisponível")
                total_fraturas = resultado.get("total_fraturas", 0)

                if total_fraturas > 0:
                    st.error(f"🔴 {predicao}")
                else:
                    st.success(f"🟢 {predicao}")

                st.write("**Fraturas detectadas:** ",total_fraturas,)

                detections = resultado.get("detecções", [])
                for indice, detection in enumerate(detections,start=1):
                    confianca = detection.get("confidence")

                    if confianca is not None:
                        st.write(f"**Fratura {indice}** - Confiança: {confianca:.2%}")

    if st.button("📄 Gerar relatório em PDF"):
        arquivos_por_indice = {
            indice: arquivo
            for indice, arquivo in enumerate(uploaded_files or [])
        }
        pdf = gerar_pdf(resposta.get("resultados", []), arquivos_por_indice)

        st.session_state["pdf"] = pdf

    if st.session_state.get("pdf") is not None:
        st.download_button(
            label="📥 Baixar PDF",
            data=st.session_state["pdf"],
            file_name="relatorio_fraturas.pdf",
            mime="application/pdf",
        )

    st.markdown("---")
    st.markdown(
        """
        <a href="#topo">
            <button style="
                width: 100%;
                padding: 0.5rem;
                border-radius: 0.5rem;
                border: 1px solid #ccc;
                background-color: transparent;
                cursor: pointer;
            ">
                ⬆️ Voltar ao topo
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )
else:
    st.info("Selecione ao menos uma imagem.")

st.markdown("---")
