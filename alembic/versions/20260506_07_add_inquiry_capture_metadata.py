"""add inquiry capture metadata

Revision ID: 20260506_07
Revises: 20260430_06
Create Date: 2026-05-06 12:20:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260506_07"
down_revision: Union[str, Sequence[str], None] = "20260430_06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def ensure_index(inspector, table_name: str, index_name: str, columns: list[str], unique: bool = False) -> None:
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in existing_indexes:
        op.create_index(index_name, table_name, columns, unique=unique)


def has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "inquiries" not in inspector.get_table_names():
        return

    if not has_column(inspector, "inquiries", "source"):
        op.add_column("inquiries", sa.Column("source", sa.String(length=100), nullable=True))
    if not has_column(inspector, "inquiries", "service_interest"):
        op.add_column("inquiries", sa.Column("service_interest", sa.String(length=255), nullable=True))
    if not has_column(inspector, "inquiries", "page_path"):
        op.add_column("inquiries", sa.Column("page_path", sa.String(length=255), nullable=True))

    ensure_index(inspector, "inquiries", op.f("ix_inquiries_source"), ["source"])
    ensure_index(inspector, "inquiries", op.f("ix_inquiries_page_path"), ["page_path"])


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    if "inquiries" not in inspector.get_table_names():
        return

    existing_indexes = {index["name"] for index in inspector.get_indexes("inquiries")}
    if op.f("ix_inquiries_page_path") in existing_indexes:
        op.drop_index(op.f("ix_inquiries_page_path"), table_name="inquiries")
    if op.f("ix_inquiries_source") in existing_indexes:
        op.drop_index(op.f("ix_inquiries_source"), table_name="inquiries")

    if has_column(inspector, "inquiries", "page_path"):
        op.drop_column("inquiries", "page_path")
    if has_column(inspector, "inquiries", "service_interest"):
        op.drop_column("inquiries", "service_interest")
    if has_column(inspector, "inquiries", "source"):
        op.drop_column("inquiries", "source")
