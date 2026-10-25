from typing import Annotated
from fastapi import APIRouter, Depends, File, UploadFile
from core import carregar_modelo, get_current_user
from usecases.PredictUseCase.Predict import Execute

router = APIRouter(
    prefix="/predict", tags=["Predição"], dependencies=[Depends(get_current_user)]
)
model = carregar_modelo()


@router.post("/predictAI")
async def PrdictAi(files: Annotated[list[UploadFile], File()]):
    conteudoAnalisado = await Execute(files, model)
    return conteudoAnalisado
