from typing import Annotated
from fastapi import APIRouter, File, UploadFile
from Src.Yolo_model.modelo_base import carregar_modelo
from Src.UseCases.PredictUseCase.PredictAiUseCase import Execute

router = APIRouter()
model = carregar_modelo()

@router.post("/predictAI")
async def PrdictAi(files: Annotated[list[UploadFile], File()]):
    conteudoAnalisado = await Execute(files, model)
    
    return conteudoAnalisado


