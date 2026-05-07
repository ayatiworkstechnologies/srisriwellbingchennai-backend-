"""add service summary and benefits fields

Revision ID: 20260507_10
Revises: 20260507_09
Create Date: 2026-05-07 19:25:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260507_10"
down_revision: Union[str, Sequence[str], None] = "20260507_09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "services" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("services")}

    if "short_description" not in existing_columns:
        op.add_column(
            "services",
            sa.Column("short_description", sa.Text(), nullable=True),
        )

    if "benefits" not in existing_columns:
        op.add_column(
            "services",
            sa.Column("benefits", sa.Text(), nullable=True),
        )

    op.execute(
        sa.text(
            """
            UPDATE services
            SET short_description = CASE
                WHEN short_description IS NULL OR TRIM(short_description) = '' THEN description
                ELSE short_description
            END
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE services
            SET benefits = CASE
                WHEN benefits IS NULL OR TRIM(benefits) = '' THEN 'Personalised care\nHolistic wellbeing support'
                ELSE benefits
            END
            """
        )
    )

    op.alter_column("services", "short_description", existing_type=sa.Text(), nullable=False)
    op.alter_column("services", "benefits", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "services" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("services")}

    if "benefits" in existing_columns:
        op.drop_column("services", "benefits")

    if "short_description" in existing_columns:
        op.drop_column("services", "short_description")
