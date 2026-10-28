from typing import Annotated
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from schemas.predict_result_schema import AnaliseCompletaResponse
from core import carregar_modelo, get_current_user, MAX_IMAGES, MENSSAGENS_ERRO
from usecases.PredictUseCase.Predict import Execute

router = APIRouter(
    prefix="/predict", tags=["Predição"], dependencies=[Depends(get_current_user)]
)
model = carregar_modelo()


@router.post(
    "/predictAI", response_model=AnaliseCompletaResponse, status_code=status.HTTP_200_OK
)
async def PredictAi(files: Annotated[list[UploadFile], File()]):
    if not 1 <= len(files) <= MAX_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=MENSSAGENS_ERRO["IMAGE_LIST_LENGTH_ERROR"],
        )
    conteudoAnalisado = await Execute(files, model)

    return conteudoAnalisado
