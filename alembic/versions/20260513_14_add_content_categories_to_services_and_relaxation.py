"""add content categories to services and relaxation therapies

Revision ID: 20260513_14
Revises: 20260511_13
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260513_14"
down_revision = "20260511_13"
branch_labels = None
depends_on = None


def ensure_index(inspector, table_name: str, index_name: str, columns: list[str]) -> None:
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in existing_indexes:
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    service_columns = {column["name"] for column in inspector.get_columns("services")}
    if "category" not in service_columns:
        op.add_column(
            "services",
            sa.Column("category", sa.String(length=50), nullable=False, server_default="main"),
        )
    ensure_index(inspector, "services", op.f("ix_services_category"), ["category"])
    op.execute("UPDATE services SET category = 'main' WHERE category IS NULL OR category = ''")

    relax_columns = {column["name"] for column in inspector.get_columns("relaxation_therapies")}
    if "category" not in relax_columns:
        op.add_column(
            "relaxation_therapies",
            sa.Column("category", sa.String(length=50), nullable=False, server_default="relax"),
        )
    ensure_index(inspector, "relaxation_therapies", op.f("ix_relaxation_therapies_category"), ["category"])
    op.execute("UPDATE relaxation_therapies SET category = 'relax' WHERE category IS NULL OR category = ''")


def downgrade() -> None:
    inspector = inspect(op.get_bind())

    relax_indexes = {index["name"] for index in inspector.get_indexes("relaxation_therapies")}
    if op.f("ix_relaxation_therapies_category") in relax_indexes:
        op.drop_index(op.f("ix_relaxation_therapies_category"), table_name="relaxation_therapies")

    relax_columns = {column["name"] for column in inspector.get_columns("relaxation_therapies")}
    if "category" in relax_columns:
        op.drop_column("relaxation_therapies", "category")

    service_indexes = {index["name"] for index in inspector.get_indexes("services")}
    if op.f("ix_services_category") in service_indexes:
        op.drop_index(op.f("ix_services_category"), table_name="services")

    service_columns = {column["name"] for column in inspector.get_columns("services")}
    if "category" in service_columns:
        op.drop_column("services", "category")
