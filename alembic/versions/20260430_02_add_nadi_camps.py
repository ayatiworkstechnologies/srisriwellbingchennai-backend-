"""add nadi camps

Revision ID: 20260430_02
Revises: 20260430_01
Create Date: 2026-04-30 17:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260430_02"
down_revision: Union[str, Sequence[str], None] = "20260430_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "nadi_camps" not in inspector.get_table_names():
        op.create_table(
            "nadi_camps",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("doctor", sa.String(length=255), nullable=False),
            sa.Column("camp_date", sa.String(length=50), nullable=False),
            sa.Column("location", sa.String(length=255), nullable=False),
            sa.Column("contact", sa.String(length=255), nullable=False),
            sa.Column("address", sa.Text(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {index["name"] for index in inspector.get_indexes("nadi_camps")}
    if op.f("ix_nadi_camps_id") not in existing_indexes:
      op.create_index(op.f("ix_nadi_camps_id"), "nadi_camps", ["id"], unique=False)
    if op.f("ix_nadi_camps_camp_date") not in existing_indexes:
      op.create_index(op.f("ix_nadi_camps_camp_date"), "nadi_camps", ["camp_date"], unique=False)
    if op.f("ix_nadi_camps_location") not in existing_indexes:
      op.create_index(op.f("ix_nadi_camps_location"), "nadi_camps", ["location"], unique=False)
    if op.f("ix_nadi_camps_sort_order") not in existing_indexes:
      op.create_index(op.f("ix_nadi_camps_sort_order"), "nadi_camps", ["sort_order"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_nadi_camps_sort_order"), table_name="nadi_camps")
    op.drop_index(op.f("ix_nadi_camps_location"), table_name="nadi_camps")
    op.drop_index(op.f("ix_nadi_camps_camp_date"), table_name="nadi_camps")
    op.drop_index(op.f("ix_nadi_camps_id"), table_name="nadi_camps")
    op.drop_table("nadi_camps")
