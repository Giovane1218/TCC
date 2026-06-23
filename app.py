import streamlit as st
import requests
from PIL import Image
import base64
from io import BytesIO


st.set_page_config(page_title="Teste 1", layout="centered")

st.title("Teste")
st.markdown("---")

uploaded_file = st.file_uploader("Selecione a imagem do Raio-X", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    bytes_data = uploaded_file.getvalue()
    base64_data = base64.b64encode(bytes_data).decode('utf-8')
    payload = {"imagem_base64": base64_data}

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original")
        st.image(image, width="stretch")

    if st.button("Analisar Imagem"):
        with st.spinner("Processando e analisando..."):
            try:
                response = requests.post("http://127.0.0.1:8000/predictAI", json=payload)

                if response.status_code == 200:
                    res = response.json()
                    imagem_base64 = res.get("imagem_processada")
                    imagem_bytes = base64.b64decode(imagem_base64) if imagem_base64 else None

                    with col2:
                        st.subheader("Resultado")
                        if imagem_bytes:
                            st.image(imagem_bytes, width="stretch")
                        else:
                            st.warning("Imagem processada não foi retornada.")

                        st.success(f"Status: {res.get('status')}")
                        st.write(f"Previsão: {res.get('predicao')}")
                else:
                    st.error(f"Erro na API: {response.status_code}")
            
            except Exception as e:
                st.error(f"Falha na conexão com o servidor: {e}")

st.markdown("---")

