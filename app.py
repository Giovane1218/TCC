import requests
import streamlit as st
import io
import base64
from PIL import Image

API_URL = "http://127.0.0.1:8000/predictAI/multiple"
REQUEST_TIMEOUT = 120
MAX_IMAGENS = 20

st.set_page_config(page_title="Análise de Raio-X", layout="wide")
st.title("Análise de imagens de Raio-X")
st.markdown("Selecione várias imagens e envie todas em uma única requisição.")
st.markdown("---")

uploaded_files = st.file_uploader(
    "Selecione as imagens de Raio-X",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if uploaded_files:
    if len(uploaded_files) > MAX_IMAGENS:
        st.error(f"Selecione no máximo {MAX_IMAGENS} imagens por envio.")
        st.stop()

    st.write(f"**{len(uploaded_files)} imagem(ns) selecionada(s).**")

    colunas = st.columns(3)
    for indice, arquivo in enumerate(uploaded_files):
        with colunas[indice % 3]:
            st.image(Image.open(arquivo), caption=arquivo.name, width="stretch")

    if st.button("Analisar imagens", type="primary", use_container_width=True):
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

        st.success(
            f"Processamento concluído: {resposta.get('sucessos', 0)} sucesso(s) "
            f"e {resposta.get('erros', 0)} erro(s)."
        )

        st.markdown("---")
        st.subheader("Resultados")

        arquivos_por_nome = {arquivo.name: arquivo for arquivo in uploaded_files}

        for resultado in resposta.get("resultados", []):
            nome = resultado.get("nome_arquivo", "Imagem")

            with st.expander(nome, expanded=True):
                col_original, col_processada = st.columns(2)

                with col_original:
                    st.markdown("#### Original")
                    arquivo = arquivos_por_nome.get(nome)
                    if arquivo is not None:
                        st.image(Image.open(arquivo), width="stretch")

                with col_processada:
                    st.markdown("#### Resultado")

                    if resultado.get("status") != "success":
                        st.error(resultado.get("erro", "Erro desconhecido"))
                        continue

                    imagem_processada = resultado.get("imagem_processada")
                    if imagem_processada:
                        st.image(
                            Image.open(io.BytesIO(base64.b64decode(imagem_processada))),
                            width="stretch",
                        )

                    st.success(f"Status: {resultado.get('status')}")
                    st.write(f"Previsão: {resultado.get('predicao')}")
                    st.caption(
                        f"Tamanho recebido: "
                        f"{resultado.get('detalhes', {}).get('tamanho_bytes', 0)} bytes"
                    )
else:
    st.info("Selecione ao menos uma imagem.")

st.markdown("---")
