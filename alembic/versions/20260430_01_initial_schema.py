"""initial schema

Revision ID: 20260430_01
Revises:
Create Date: 2026-04-30 15:15:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260430_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def ensure_index(inspector, table_name: str, index_name: str, columns: list[str], unique: bool = False) -> None:
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in existing_indexes:
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "admin_users" not in existing_tables:
        op.create_table(
            "admin_users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    ensure_index(inspector, "admin_users", op.f("ix_admin_users_email"), ["email"], unique=True)
    ensure_index(inspector, "admin_users", op.f("ix_admin_users_id"), ["id"])

    if "inquiries" not in existing_tables:
        op.create_table(
            "inquiries",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("phone", sa.String(length=50), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("topic", sa.String(length=100), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    ensure_index(inspector, "inquiries", op.f("ix_inquiries_created_at"), ["created_at"])
    ensure_index(inspector, "inquiries", op.f("ix_inquiries_email"), ["email"])
    ensure_index(inspector, "inquiries", op.f("ix_inquiries_id"), ["id"])
    ensure_index(inspector, "inquiries", op.f("ix_inquiries_status"), ["status"])

    if "services" not in existing_tables:
        op.create_table(
            "services",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("image", sa.String(length=255), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    ensure_index(inspector, "services", op.f("ix_services_id"), ["id"])
    ensure_index(inspector, "services", op.f("ix_services_sort_order"), ["sort_order"])

    if "testimonials" not in existing_tables:
        op.create_table(
            "testimonials",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("review", sa.Text(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    ensure_index(inspector, "testimonials", op.f("ix_testimonials_id"), ["id"])
    ensure_index(inspector, "testimonials", op.f("ix_testimonials_sort_order"), ["sort_order"])


def downgrade() -> None:
    op.drop_index(op.f("ix_testimonials_sort_order"), table_name="testimonials")
    op.drop_index(op.f("ix_testimonials_id"), table_name="testimonials")
    op.drop_table("testimonials")

    op.drop_index(op.f("ix_services_sort_order"), table_name="services")
    op.drop_index(op.f("ix_services_id"), table_name="services")
    op.drop_table("services")

    op.drop_index(op.f("ix_inquiries_status"), table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_id"), table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_email"), table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_created_at"), table_name="inquiries")
    op.drop_table("inquiries")

    op.drop_index(op.f("ix_admin_users_id"), table_name="admin_users")
    op.drop_index(op.f("ix_admin_users_email"), table_name="admin_users")
    op.drop_table("admin_users")
