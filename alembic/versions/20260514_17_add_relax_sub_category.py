"""add relax sub category

Revision ID: 20260514_17
Revises: 20260513_16
Create Date: 2026-05-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260514_17"
down_revision: Union[str, None] = "20260513_16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RENEWAL_TITLES = ("Shirolepa", "Keshavarna", "Mukhalepa")


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "content_categories" in inspector.get_table_names():
        existing = connection.execute(
            sa.text("SELECT id FROM content_categories WHERE slug = :slug"),
            {"slug": "relax-sub"},
        ).first()
        if not existing:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO content_categories
                        (slug, label, description, sort_order, is_active, created_at)
                    VALUES
                        (:slug, :label, :description, :sort_order, :is_active, CURRENT_TIMESTAMP)
                    """
                ),
                {
                    "slug": "relax-sub",
                    "label": "Relax Sub",
                    "description": "Head, hair, and facial renewal therapy content.",
                    "sort_order": 3,
                    "is_active": "true",
                },
            )

    if "relaxation_therapies" in inspector.get_table_names():
        connection.execute(
            sa.text(
                "UPDATE relaxation_therapies SET category = :category WHERE title IN :titles"
            ).bindparams(sa.bindparam("titles", expanding=True)),
            {"category": "relax-sub", "titles": RENEWAL_TITLES},
        )

    if "services" in inspector.get_table_names():
        connection.execute(
            sa.text(
                "UPDATE services SET category = :category WHERE title IN :titles"
            ).bindparams(sa.bindparam("titles", expanding=True)),
            {"category": "relax-sub", "titles": RENEWAL_TITLES},
        )


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "relaxation_therapies" in inspector.get_table_names():
        connection.execute(
            sa.text(
                "UPDATE relaxation_therapies SET category = :category WHERE title IN :titles"
            ).bindparams(sa.bindparam("titles", expanding=True)),
            {"category": "relax", "titles": RENEWAL_TITLES},
        )

    if "services" in inspector.get_table_names():
        connection.execute(
            sa.text(
                "UPDATE services SET category = :category WHERE title IN :titles"
            ).bindparams(sa.bindparam("titles", expanding=True)),
            {"category": "relax", "titles": RENEWAL_TITLES},
        )

    if "content_categories" in inspector.get_table_names():
        connection.execute(
            sa.text("DELETE FROM content_categories WHERE slug = :slug"),
            {"slug": "relax-sub"},
        )
