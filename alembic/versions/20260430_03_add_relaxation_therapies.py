"""add relaxation therapies

Revision ID: 20260430_03
Revises: 20260430_02
Create Date: 2026-04-30 18:05:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260430_03"
down_revision: Union[str, Sequence[str], None] = "20260430_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "relaxation_therapies" not in inspector.get_table_names():
        op.create_table(
            "relaxation_therapies",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("duration", sa.String(length=50), nullable=False),
            sa.Column("short_description", sa.Text(), nullable=False),
            sa.Column("details", sa.Text(), nullable=False),
            sa.Column("benefits", sa.Text(), nullable=False),
            sa.Column("image", sa.String(length=255), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {index["name"] for index in inspector.get_indexes("relaxation_therapies")}
    if op.f("ix_relaxation_therapies_id") not in existing_indexes:
        op.create_index(op.f("ix_relaxation_therapies_id"), "relaxation_therapies", ["id"], unique=False)
    if op.f("ix_relaxation_therapies_sort_order") not in existing_indexes:
        op.create_index(op.f("ix_relaxation_therapies_sort_order"), "relaxation_therapies", ["sort_order"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_relaxation_therapies_sort_order"), table_name="relaxation_therapies")
    op.drop_index(op.f("ix_relaxation_therapies_id"), table_name="relaxation_therapies")
    op.drop_table("relaxation_therapies")
