import base64
from typing import List

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

from .image_utils import processar_imagem
from modelo.tentativa_1.modelo_base import carregar_modelo, prever_imagem

router = APIRouter()
MODEL = carregar_modelo()


def processar_analisar(content: bytes) -> dict:
    if not content:
        raise ValueError("Imagem vazia")

    imagem_processada = processar_imagem(content, 512)
    imagem_retorno = (imagem_processada[0, :, :, 0] * 255).astype(np.uint8)

    sucesso, buffer = cv2.imencode(".png", imagem_retorno)
    if not sucesso:
        raise ValueError("Não foi possível codificar a imagem processada")

    diagnostico = prever_imagem(imagem_processada, model=MODEL)
    return {
        "status": "success",
        "predicao": diagnostico.get("resultado", "Nenhum resultado"),
        "probabilidade": diagnostico.get("probabilidade", 0.0),
        "imagem_processada": base64.b64encode(buffer).decode("utf-8"),
        "detalhes": {"tamanho_bytes": len(content)},
    }


@router.post("/predictAI")
async def predict(file: UploadFile = File(...)):
    """Recebe uma imagem em multipart."""
    try:
        content = await file.read()
        return processar_analisar(content)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar imagem",
        )


@router.post("/predictAI/multiple")
async def predictAll(files: List[UploadFile] = File(...)):
    """Recebe várias imagens em multipart."""
    if not files:
        raise HTTPException(status_code=400, detail="Nenhuma imagem enviada")

    resultados = []
    for indice, file in enumerate(files):
        try:
            content = await file.read()
            resultado = processar_analisar(content)
            resultado.update({
                "indice": indice,
                "nome_arquivo": file.filename or f"imagem_{indice + 1}",
            })
        except ValueError as erro:
            resultado = {
                "indice": indice,
                "nome_arquivo": file.filename or f"imagem_{indice + 1}",
                "status": "error",
                "erro": str(erro),
            }
        except Exception:
            resultado = {
                "indice": indice,
                "nome_arquivo": file.filename or f"imagem_{indice + 1}",
                "status": "error",
                "erro": "Erro interno ao processar imagem",
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
