from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_model import UsuarioModel
from repositories.user_repository import get_user_by_email, update_user
from schemas.user_schema import UsuarioUpdate


async def ExecuteUpdateUser(
    db: AsyncSession, dados: UsuarioUpdate, email: str
) -> UsuarioModel:
    user = await get_user_by_email(db, email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    user.username = dados.username
    user.email = str(dados.email)
    user.registro_profissional = dados.registro_profissional
    user.cargo = dados.cargo
    user.uf_registro = dados.uf_registro.upper()
    user.ativo = dados.ativo

    try:
        await update_user(db, user)
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe usuario com esse email ou registro profissional.",
        ) from None

    return user
