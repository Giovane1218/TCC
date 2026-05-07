import base64
from fastapi import HTTPException, APIRouter
import random
from model.imagem_model import ImagemRequest
from .image_utils import processar_imagem

router = APIRouter() 

@router.post("/predictAI")
async def predictAI(req: ImagemRequest):
    try:
        try:
            content = base64.b64decode(req.imagem_base64)
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

        nome_arquivo = processar_imagem(content)

        respostas = ["Fratura detectada", "Nenhuma fratura detectada"]
        analise_texto = random.choice(respostas)

        resultado = {
            "status": "success",
            "arquivo_processado": nome_arquivo,
            "predicao": analise_texto,
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
    
