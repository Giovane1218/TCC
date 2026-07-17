import random
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile

from .image_utils import processar_imagem

app = FastAPI()

MAX_FILE_SIZE = 10 * 1024 * 1024
TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/jpg"}


async def analisar_arquivo(file: UploadFile) -> dict:
    if file.content_type not in TIPOS_PERMITIDOS:
        raise ValueError("Formato inválido. Aceito: JPG, JPEG e PNG")

    content = await file.read()

    if not content:
        raise ValueError("Arquivo vazio")

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("Arquivo maior que 10 MB")

    # Valida e prepara a imagem para o futuro modelo.
    processar_imagem(content)

    respostas = ["Fratura detectada", "Nenhuma fratura detectada"]

    return {
        "status": "success",
        "nome_arquivo": file.filename,
        "predicao": random.choice(respostas),
        "detalhes": {
            "tipo_formato": file.content_type,
            "tamanho_bytes": len(content),
        },
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Rota original para uma única imagem."""
    try:
        return await analisar_arquivo(file)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar a imagem",
        ) from erro


@app.post("/predict/multiple")
async def predict_multiple(files: List[UploadFile] = File(...)):
    """Recebe várias imagens no mesmo formulário multipart."""
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Máximo de 20 imagens por envio")

    resultados = []

    for indice, file in enumerate(files):
        try:
            resultado = await analisar_arquivo(file)
            resultado["indice"] = indice
        except ValueError as erro:
            resultado = {
                "indice": indice,
                "nome_arquivo": file.filename,
                "status": "error",
                "erro": str(erro),
            }
        except Exception:
            resultado = {
                "indice": indice,
                "nome_arquivo": file.filename,
                "status": "error",
                "erro": "Erro interno ao processar a imagem",
            }

        resultados.append(resultado)

    sucessos = sum(item["status"] == "success" for item in resultados)

    return {
        "status": "success" if sucessos == len(resultados) else "partial_success",
        "total": len(resultados),
        "sucessos": sucessos,
        "erros": len(resultados) - sucessos,
        "resultados": resultados,
    }
