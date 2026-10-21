from services.token_services import create_access_token
from core import LoginError, ClassificarErro
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user_model import UsuarioModel
from services.password_services import verify_password

async def ExecuteLogin(db: AsyncSession, email: str, password: str) -> dict[str, str]:
    try:
        user = await db.scalar(select(UsuarioModel).where(UsuarioModel.email == email))
        if user is None or not user.ativo or not verify_password(password, user.senha_hash):
            raise LoginError()
        token = create_access_token(user.user_identifier)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as ex:
        status_code, mensagem = ClassificarErro(ex)
        headers = {"WWW-Authenticate": "Bearer"} if status_code == status.HTTP_401_UNAUTHORIZED else None
        raise HTTPException(status_code=status_code, detail=mensagem, headers=headers) from ex
