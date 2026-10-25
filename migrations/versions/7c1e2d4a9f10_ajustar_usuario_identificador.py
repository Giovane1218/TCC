"""Ajusta identificador, username e email de usuarios.

Revision ID: 7c1e2d4a9f10
Revises: 5fbf4ba41be2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c1e2d4a9f10"
down_revision: Union[str, Sequence[str], None] = "5fbf4ba41be2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "usuarios",
        "user_name",
        new_column_name="username",
        existing_type=sa.String(length=120),
        existing_nullable=False,
    )
    op.alter_column(
        "usuarios",
        "user_indentifier",
        new_column_name="user_identifier",
        existing_type=sa.String(length=36),
        existing_nullable=False,
    )
    op.alter_column(
        "usuarios",
        "email",
        existing_type=sa.String(length=80),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "usuarios",
        "email",
        existing_type=sa.String(length=80),
        nullable=True,
    )
    op.alter_column(
        "usuarios",
        "user_identifier",
        new_column_name="user_indentifier",
        existing_type=sa.String(length=36),
        existing_nullable=False,
    )
    op.alter_column(
        "usuarios",
        "username",
        new_column_name="user_name",
        existing_type=sa.String(length=120),
        existing_nullable=False,
    )
