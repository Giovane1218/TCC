import os

from sqlalchemy import select

from core import ADMIN_LEVEL
from services.password_services import hash_password
from services.token_services import _token_secret
from database.data_base import Base, SessionLocal, engine
from models.user_model import UsuarioModel
from sqlalchemy.ext.asyncio import AsyncSession


async def initialize_authentication() -> None:
    _token_secret()

    async with SessionLocal.begin() as db:
        admin = await db.scalar(
            select(UsuarioModel)
            .where(UsuarioModel.nivel_acesso == ADMIN_LEVEL)
            .limit(1)
        )
        if admin is not None:
            return
        username = os.getenv("ADMIN_USERNAME")
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")
        registro = os.getenv("ADMIN_REGISTRO_PROFISSIONAL")
        cargo = os.getenv("ADMIN_CARGO")
        uf_registro = os.getenv("ADMIN_UF_REGISTRO")

        if not all((username, email, password, registro, cargo, uf_registro)):
            raise RuntimeError(
                "Não existe administrador. Configure ADMIN_USERNAME, "
                "ADMIN_EMAIL, ADMIN_PASSWORD, "
                "ADMIN_REGISTRO_PROFISSIONAL, ADMIN_CARGO e ADMIN_UF_REGISTRO "
                "para criar o primeiro."
            )
        if len(password) < 12:
            raise RuntimeError("ADMIN_PASSWORD precisa ter pelo menos 12 caracteres.")
        if len(uf_registro) != 2:
            raise RuntimeError("ADMIN_UF_REGISTRO precisa conter exatamente 2 letras.")

        db.add(
            UsuarioModel(
                username=username,
                email=email,
                senha_hash=hash_password(password),
                nivel_acesso=ADMIN_LEVEL,
                registro_profissional=registro,
                cargo=cargo,
                uf_registro=uf_registro.upper(),
                ativo=True,
            )
        )


async def add_user(db: AsyncSession, usuario: UsuarioModel) -> UsuarioModel:
    await db.add(usuario)
    await db.flush()
    return usuario


async def get_user_by_email(db: AsyncSession, email: str) -> UsuarioModel | None:
    result = await db.scalar(select(UsuarioModel).where(UsuarioModel.email == email))
    return result


async def update_user(db: AsyncSession, usuario: UsuarioModel) -> UsuarioModel:
    await db.flush()
    return usuario


async def delete_user(db: AsyncSession, usuario: UsuarioModel):
    await db.delete(usuario)
    await db.flush()
