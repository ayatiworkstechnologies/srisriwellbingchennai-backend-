"""add alternative and panchakarma tables

Revision ID: 20260430_04
Revises: 20260430_03
Create Date: 2026-04-30 19:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260430_04"
down_revision: Union[str, Sequence[str], None] = "20260430_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def ensure_index(inspector, table_name: str, index_name: str, columns: list[str]) -> None:
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in existing_indexes:
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "alternative_treatments" not in inspector.get_table_names():
        op.create_table(
            "alternative_treatments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("item_id", sa.String(length=255), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=255), nullable=False),
            sa.Column("short_desc", sa.Text(), nullable=False),
            sa.Column("image", sa.String(length=255), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_unique_constraint("uq_alternative_treatments_item_id", "alternative_treatments", ["item_id"])
    ensure_index(inspector, "alternative_treatments", op.f("ix_alternative_treatments_id"), ["id"])
    ensure_index(inspector, "alternative_treatments", op.f("ix_alternative_treatments_item_id"), ["item_id"])
    ensure_index(inspector, "alternative_treatments", op.f("ix_alternative_treatments_category"), ["category"])
    ensure_index(inspector, "alternative_treatments", op.f("ix_alternative_treatments_sort_order"), ["sort_order"])

    if "panchakarma_core_therapies" not in inspector.get_table_names():
        op.create_table(
            "panchakarma_core_therapies",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("item_id", sa.String(length=255), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("dosha", sa.String(length=255), nullable=False),
            sa.Column("dosha_color", sa.String(length=255), nullable=False),
            sa.Column("dosha_bg", sa.String(length=255), nullable=False),
            sa.Column("dosha_border", sa.String(length=255), nullable=False),
            sa.Column("short_desc", sa.Text(), nullable=False),
            sa.Column("image", sa.String(length=255), nullable=False),
            sa.Column("benefits", sa.Text(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_unique_constraint("uq_panchakarma_core_therapies_item_id", "panchakarma_core_therapies", ["item_id"])
    ensure_index(inspector, "panchakarma_core_therapies", op.f("ix_panchakarma_core_therapies_id"), ["id"])
    ensure_index(inspector, "panchakarma_core_therapies", op.f("ix_panchakarma_core_therapies_item_id"), ["item_id"])
    ensure_index(inspector, "panchakarma_core_therapies", op.f("ix_panchakarma_core_therapies_sort_order"), ["sort_order"])

    if "panchakarma_other_treatments" not in inspector.get_table_names():
        op.create_table(
            "panchakarma_other_treatments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=255), nullable=False),
            sa.Column("desc", sa.Text(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    ensure_index(inspector, "panchakarma_other_treatments", op.f("ix_panchakarma_other_treatments_id"), ["id"])
    ensure_index(inspector, "panchakarma_other_treatments", op.f("ix_panchakarma_other_treatments_category"), ["category"])
    ensure_index(inspector, "panchakarma_other_treatments", op.f("ix_panchakarma_other_treatments_sort_order"), ["sort_order"])


def downgrade() -> None:
    op.drop_index(op.f("ix_panchakarma_other_treatments_sort_order"), table_name="panchakarma_other_treatments")
    op.drop_index(op.f("ix_panchakarma_other_treatments_category"), table_name="panchakarma_other_treatments")
    op.drop_index(op.f("ix_panchakarma_other_treatments_id"), table_name="panchakarma_other_treatments")
    op.drop_table("panchakarma_other_treatments")

    op.drop_index(op.f("ix_panchakarma_core_therapies_sort_order"), table_name="panchakarma_core_therapies")
    op.drop_index(op.f("ix_panchakarma_core_therapies_item_id"), table_name="panchakarma_core_therapies")
    op.drop_index(op.f("ix_panchakarma_core_therapies_id"), table_name="panchakarma_core_therapies")
    op.drop_table("panchakarma_core_therapies")

    op.drop_index(op.f("ix_alternative_treatments_sort_order"), table_name="alternative_treatments")
    op.drop_index(op.f("ix_alternative_treatments_category"), table_name="alternative_treatments")
    op.drop_index(op.f("ix_alternative_treatments_item_id"), table_name="alternative_treatments")
    op.drop_index(op.f("ix_alternative_treatments_id"), table_name="alternative_treatments")
    op.drop_table("alternative_treatments")
