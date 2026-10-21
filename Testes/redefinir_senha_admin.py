import asyncio
import os
from getpass import getpass

from sqlalchemy import select

from database.data_base import SessionLocal
from models.user_model import UsuarioModel
from services.password_services import hash_password


async def redefinir_senha() -> None:
    username = os.getenv("ADMIN_USERNAME")
    if not username:
        raise RuntimeError("ADMIN_USERNAME não está configurado no .env.")

    password = getpass("Nova senha do administrador (mínimo 12 caracteres): ")
    confirmation = getpass("Confirme a nova senha: ")
    if len(password) < 12:
        raise ValueError("A senha precisa ter pelo menos 12 caracteres.")
    if password != confirmation:
        raise ValueError("As senhas não correspondem.")

    async with SessionLocal.begin() as db:
        admin = await db.scalar(
            select(UsuarioModel).where(UsuarioModel.username == username)
        )
        if admin is None or admin.nivel_acesso != 1:
            raise RuntimeError("O admin configurado não foi encontrado no banco.")
        admin.senha_hash = hash_password(password)


asyncio.run(redefinir_senha())
