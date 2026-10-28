from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from usecases.ReportUseCase.report_useCase import ExecuteGerarPdf
from database.data_base import get_db
from schemas.report_schema import ReportRequest
from core.Security.security import get_current_user
from models.user_model import UsuarioModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/reports", tags=["Relatórios"])


@router.get("/reportpdf", status_code=status.HTTP_200_OK)
async def GerarReport(
    db: Annotated[AsyncSession, Depends(get_db)],
    usuarioAtual: Annotated[UsuarioModel, Depends(get_current_user)],
    dados: ReportRequest,
):
    pdf = await ExecuteGerarPdf(
        db, usuarioAtual, dados.pacienteInfo, dados.resultadosInfo
    )

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="relatorio.pdf"'},
    )
