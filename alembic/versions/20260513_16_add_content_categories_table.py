"""add content categories table

Revision ID: 20260513_16
Revises: 20260513_15
Create Date: 2026-05-13 18:40:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260513_16"
down_revision: Union[str, Sequence[str], None] = "20260513_15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "content_categories" not in inspector.get_table_names():
        op.create_table(
            "content_categories",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("slug", sa.String(length=50), nullable=False),
            sa.Column("label", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.String(length=10), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_content_categories_id", "content_categories", ["id"], unique=False)
        op.create_index("ix_content_categories_slug", "content_categories", ["slug"], unique=True)
        op.create_index("ix_content_categories_sort_order", "content_categories", ["sort_order"], unique=False)

        defaults = [
            ("main", "Main", "Homepage and main therapy/service content.", 1),
            ("relax", "Relax", "Relaxation therapy and renewal content.", 2),
            ("panchakarma", "Panchakarma", "Panchakarma and detox-related content.", 3),
        ]
        for slug, label, description, sort_order in defaults:
            bind.execute(
                sa.text(
                    "INSERT INTO content_categories (slug, label, description, sort_order, is_active, created_at) "
                    "VALUES (:slug, :label, :description, :sort_order, 'true', CURRENT_TIMESTAMP)"
                ),
                {
                    "slug": slug,
                    "label": label,
                    "description": description,
                    "sort_order": sort_order,
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "content_categories" not in inspector.get_table_names():
        return

    op.drop_index("ix_content_categories_sort_order", table_name="content_categories")
    op.drop_index("ix_content_categories_slug", table_name="content_categories")
    op.drop_index("ix_content_categories_id", table_name="content_categories")
    op.drop_table("content_categories")
