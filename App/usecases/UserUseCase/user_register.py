from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.user_schema import UsuarioRequest
from repositories.user_repository import add_user
from core.config import USER_LEVEL
from models.user_model import UsuarioModel
from services.password_services import hash_password


async def ExecuteCreateUser(db: AsyncSession, dados: UsuarioRequest) -> UsuarioModel:
    if len(dados.password) < 12:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A senha precisa ter pelo menos 12 caracteres.",
        )

    user = UsuarioModel(
        username=dados.username,
        email=dados.email,
        senha_hash=hash_password(dados.password),
        nivel_acesso=USER_LEVEL,
        registro_profissional=dados.registro_profissional,
        cargo=dados.cargo,
        uf_registro=dados.uf_registro.upper(),
        ativo=True,
    )

    try:
        await add_user(db, user)
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe usuário com esse nome ou registro profissional.",
        ) from None

    return user
