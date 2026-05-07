"""add admin roles and therapist links

Revision ID: 20260507_08
Revises: 20260506_07
Create Date: 2026-05-07 15:40:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260507_08"
down_revision: Union[str, Sequence[str], None] = "20260506_07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def ensure_index(inspector, table_name: str, index_name: str, columns: list[str], unique: bool = False) -> None:
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in existing_indexes:
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "admin_users" in inspector.get_table_names():
        if not has_column(inspector, "admin_users", "role"):
            op.add_column("admin_users", sa.Column("role", sa.String(length=32), nullable=False, server_default="super_admin"))
        if not has_column(inspector, "admin_users", "therapist_id"):
            op.add_column("admin_users", sa.Column("therapist_id", sa.Integer(), nullable=True))
        if not has_column(inspector, "admin_users", "is_active"):
            op.add_column("admin_users", sa.Column("is_active", sa.String(length=10), nullable=False, server_default="true"))
        ensure_index(inspector, "admin_users", op.f("ix_admin_users_role"), ["role"])
        ensure_index(inspector, "admin_users", op.f("ix_admin_users_therapist_id"), ["therapist_id"])


def downgrade() -> None:
    inspector = inspect(op.get_bind())

    if "admin_users" in inspector.get_table_names():
        indexes = {index["name"] for index in inspector.get_indexes("admin_users")}
        if op.f("ix_admin_users_therapist_id") in indexes:
            op.drop_index(op.f("ix_admin_users_therapist_id"), table_name="admin_users")
        if op.f("ix_admin_users_role") in indexes:
            op.drop_index(op.f("ix_admin_users_role"), table_name="admin_users")
        if has_column(inspector, "admin_users", "is_active"):
            op.drop_column("admin_users", "is_active")
        if has_column(inspector, "admin_users", "therapist_id"):
            op.drop_column("admin_users", "therapist_id")
        if has_column(inspector, "admin_users", "role"):
            op.drop_column("admin_users", "role")
