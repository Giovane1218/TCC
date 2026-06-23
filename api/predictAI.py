import base64
from pathlib import Path
import cv2
from fastapi import HTTPException, APIRouter
import random

import numpy as np
from model.imagem_model import ImagemRequest
from .image_utils import processar_imagem

router = APIRouter()
imagems_dir = Path(__file__).resolve().parent.parent / "imagens"

@router.post("/predictAI")
async def predictAI(req: ImagemRequest):
    try:
 
        try:
            content = base64.b64decode(req.imagem_base64)
            print("Bytes recebidos:", len(content))
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Base64 inválido"
            )

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Imagem vazia"
            )

        imagem_processada = processar_imagem(content)

        imagem_saida = (imagem_processada[0, :, :, 0] * 255).astype(np.uint8)

        _, buffer = cv2.imencode('.png', imagem_saida)

        img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')

        respostas = ["Fratura detectada", "Nenhuma fratura detectada"]
        analise_texto = random.choice(respostas)

        resultado = {
            "status": "success",
            "predicao": analise_texto,
            "imagem_processada" : img_base64,
            "detalhes": {
                "tamanho_bytes": len(content)
            }
        }

        return resultado

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar imagem"
        )
    
