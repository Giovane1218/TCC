from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.user_schema import LoginRequest, TokenResponse
from database.data_base import get_db
from usecases.AuthUseCase.login import ExecuteLogin

router = APIRouter(prefix="/auth", tags=["Autenticação"])


# ==================================LOGIN==========================================
@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def Login(
    form: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    userLog = await ExecuteLogin(db, form.email, form.password)
    return userLog
