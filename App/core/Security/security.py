from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions.exceptions_filter import ClassificarErro
from core.exceptions.exceptions_type import LoggedOutError
from database.data_base import get_db
from models.user_model import UsuarioModel
from services.token_services import _decode_access_token

bearerScheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearerScheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsuarioModel:
    try:
        if credentials is None:
            raise LoggedOutError()

        user_identifier = _decode_access_token(credentials.credentials)
        user = await db.scalar(
            select(UsuarioModel).where(UsuarioModel.user_identifier == user_identifier)
        )
        if user is None or not user.ativo:
            raise LoggedOutError()
        return user
    except Exception as ex:
        status_code, mensagem = ClassificarErro(ex)
        raise HTTPException(
            status_code=status_code,
            detail=mensagem,
            headers={"WWW-Authenticate": "Bearer"}
            if status_code == status.HTTP_401_UNAUTHORIZED
            else None,
        ) from ex
