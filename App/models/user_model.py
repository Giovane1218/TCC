from datetime import datetime
import uuid
from sqlalchemy import Boolean, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column
from database.data_base import Base


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(String(120), unique=False, nullable=False)

    email: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    nivel_acesso: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    registro_profissional: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )

    cargo: Mapped[str] = mapped_column(String(100), nullable=False)

    uf_registro: Mapped[str] = mapped_column(String(2), nullable=False)

    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user_identifier: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
