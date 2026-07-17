import base64
import binascii
import random
from typing import List

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .image_utils import processar_imagem

router = APIRouter()


class ImagemRequest(BaseModel):
    imagem_base64: str


class ImagemMultiplaItem(BaseModel):
    nome_arquivo: str = Field(min_length=1)
    imagem_base64: str


class ImagensRequest(BaseModel):
    imagens: List[ImagemMultiplaItem] = Field(min_length=1, max_length=20)


def analisar_conteudo(content: bytes) -> dict:
    """Processa uma imagem e cria a resposta usada pelas duas rotas."""
    if not content:
        raise ValueError("Imagem vazia")

    imagem_processada = processar_imagem(content)
    imagem_saida = (imagem_processada[0, :, :, 0] * 255).astype(np.uint8)

    sucesso, buffer = cv2.imencode(".png", imagem_saida)
    if not sucesso:
        raise ValueError("Não foi possível codificar a imagem processada")

    respostas = ["Fratura detectada", "Nenhuma fratura detectada"]

    return {
        "status": "success",
        "predicao": random.choice(respostas),
        "imagem_processada": base64.b64encode(buffer.tobytes()).decode("utf-8"),
        "detalhes": {"tamanho_bytes": len(content)},
    }


def decodificar_base64(valor: str) -> bytes:
    try:
        return base64.b64decode(valor, validate=True)
    except (binascii.Error, ValueError, TypeError) as erro:
        raise ValueError("Base64 inválido") from erro


@router.post("/predictAI")
async def predict_ai(req: ImagemRequest):
    """Mantém compatibilidade com o envio de uma única imagem."""
    try:
        return analisar_conteudo(decodificar_base64(req.imagem_base64))
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar imagem",
        ) from erro


@router.post("/predictAI/multiple")
async def predict_ai_multiple(req: ImagensRequest):
    """Recebe várias imagens e devolve um resultado para cada uma."""
    resultados = []

    for indice, item in enumerate(req.imagens):
        try:
            content = decodificar_base64(item.imagem_base64)
            resultado = analisar_conteudo(content)
            resultado.update(
                {
                    "indice": indice,
                    "nome_arquivo": item.nome_arquivo,
                }
            )
        except ValueError as erro:
            resultado = {
                "indice": indice,
                "nome_arquivo": item.nome_arquivo,
                "status": "error",
                "erro": str(erro),
            }
        except Exception:
            resultado = {
                "indice": indice,
                "nome_arquivo": item.nome_arquivo,
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
