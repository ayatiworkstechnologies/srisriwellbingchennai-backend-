"""initial schema

Revision ID: 20260430_01
Revises:
Create Date: 2026-04-30 15:15:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260430_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_users_email"), "admin_users", ["email"], unique=True)
    op.create_index(op.f("ix_admin_users_id"), "admin_users", ["id"], unique=False)

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
    op.create_index(op.f("ix_inquiries_created_at"), "inquiries", ["created_at"], unique=False)
    op.create_index(op.f("ix_inquiries_email"), "inquiries", ["email"], unique=False)
    op.create_index(op.f("ix_inquiries_id"), "inquiries", ["id"], unique=False)
    op.create_index(op.f("ix_inquiries_status"), "inquiries", ["status"], unique=False)

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
    op.create_index(op.f("ix_services_id"), "services", ["id"], unique=False)
    op.create_index(op.f("ix_services_sort_order"), "services", ["sort_order"], unique=False)

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
    op.create_index(op.f("ix_testimonials_id"), "testimonials", ["id"], unique=False)
    op.create_index(op.f("ix_testimonials_sort_order"), "testimonials", ["sort_order"], unique=False)


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
