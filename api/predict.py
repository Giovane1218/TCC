from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import random

from .image_utils import processar_imagem

app = FastAPI()

MAX_FILE_SIZE = 10 * 1024 * 1024 

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # Validar tipo de arquivo
        if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(
                status_code=400, 
                detail="Formato de arquivo inválido. Aceito: JPG, PNG"
            )
        
        # Ler conteúdo do arquivo
        content = await file.read()
        
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        
        nome_arquivo = processar_imagem(content)

        # TODO: Integrar seu modelo de IA aqui
        respostas = ["Fratura detectada", "Nenhuma fratura detectada"]
        analise_texto = random.choice(respostas)

        resultado = {
            "status": "success",
            "arquivo_processado": nome_arquivo,
            "predicao": analise_texto,
            "detalhes": {
                "tipo_formato": file.content_type,
                "tamanho_bytes": len(content)
            }
        }

        return resultado

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Imagem inválida: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem: {str(e)}")
