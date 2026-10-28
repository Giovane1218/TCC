from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from core import MENSSAGENS_ERRO
from models.user_model import UsuarioModel
from schemas.user_schema import (
    UsuarioDetalhadoResponse,
    UsuarioRequest,
    UsuarioResponse,
    UsuarioUpdate,
)
from database.data_base import get_db
from core import ADMIN_LEVEL, get_current_user
from repositories.user_repository import get_user_by_email
from usecases.UserUseCase.user_delete import ExecuteDeleteUser
from usecases.UserUseCase.user_register import ExecuteCreateUser
from usecases.UserUseCase.user_update import ExecuteUpdateUser

router = APIRouter(prefix="/user", tags=["Usuário"])


# ============================USUÁRIO AUTENTICADO========================================
@router.get("/me", response_model=UsuarioDetalhadoResponse)
async def ObterUsuarioAtual(
    usuario_atual: Annotated[UsuarioModel, Depends(get_current_user)],
):
    return usuario_atual


# ============================BUSCAR USUÁRIO==============================================
@router.get("/userByEmail", response_model=UsuarioDetalhadoResponse)
async def BuscarUsuario(
    email: EmailStr,
    usuario_atual: Annotated[UsuarioModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if usuario_atual.nivel_acesso != ADMIN_LEVEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MENSSAGENS_ERRO["FORBIDDEN"],
        )
    usuario = await get_user_by_email(db, str(email))
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )
    return usuario


# ============================CRIAR USUÁRIO=======================================
@router.post(
    "/userRegister", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED
)
async def CriarUsusario(
    dados: UsuarioRequest,
    usuario_atual: Annotated[UsuarioModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if usuario_atual.nivel_acesso != ADMIN_LEVEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MENSSAGENS_ERRO["FORBIDDEN"],
        )
    response = await ExecuteCreateUser(db, dados)
    return response


# ============================ATUALIZAR USUÁRIO==========================================
@router.put("/userUpdate_email", status_code=status.HTTP_204_NO_CONTENT)
async def UpdateUsuario(
    email: EmailStr,
    dados: UsuarioUpdate,
    usuario_atual: Annotated[UsuarioModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if usuario_atual.nivel_acesso != ADMIN_LEVEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MENSSAGENS_ERRO["FORBIDDEN"],
        )
    await ExecuteUpdateUser(db, dados, email)
    return


# ============================DELETAR USUÁRIO============================================
@router.delete(
    "/userDelete_email",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def DeleteUsuario(
    email: EmailStr,
    usuario_atual: Annotated[UsuarioModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if usuario_atual.nivel_acesso != ADMIN_LEVEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MENSSAGENS_ERRO["FORBIDDEN"],
        )
    await ExecuteDeleteUser(db, email)
    return
