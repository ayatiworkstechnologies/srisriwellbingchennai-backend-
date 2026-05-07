"""add therapist profile display fields

Revision ID: 20260507_11
Revises: 20260507_10
Create Date: 2026-05-07 20:10:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260507_11"
down_revision: Union[str, Sequence[str], None] = "20260507_10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "therapists" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("therapists")}

    additions = [
        ("role_label", sa.String(length=100), "Therapist"),
        ("qualification", sa.String(length=255), ""),
        ("experience_years", sa.Integer(), "0"),
        ("languages", sa.Text(), ""),
        ("image", sa.String(length=255), "/images/doctor-placeholder.png"),
    ]

    for name, column_type, default_value in additions:
        if name not in existing_columns:
            op.add_column(
                "therapists",
                sa.Column(name, column_type, nullable=False, server_default=default_value),
            )

    op.alter_column("therapists", "role_label", server_default=None)
    op.alter_column("therapists", "qualification", server_default=None)
    op.alter_column("therapists", "experience_years", server_default=None)
    op.alter_column("therapists", "languages", server_default=None)
    op.alter_column("therapists", "image", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "therapists" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("therapists")}

    for name in ["image", "languages", "experience_years", "qualification", "role_label"]:
        if name in existing_columns:
            op.drop_column("therapists", name)
