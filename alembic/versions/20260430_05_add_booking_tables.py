"""add booking slots and therapy bookings

Revision ID: 20260430_05
Revises: 20260430_04
Create Date: 2026-04-30 23:10:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260430_05"
down_revision: Union[str, Sequence[str], None] = "20260430_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def ensure_index(inspector, table_name: str, index_name: str, columns: list[str], unique: bool = False) -> None:
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in existing_indexes:
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "booking_slots" not in inspector.get_table_names():
        op.create_table(
            "booking_slots",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("therapy_name", sa.String(length=255), nullable=False),
            sa.Column("booking_date", sa.Date(), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=False),
            sa.Column("end_time", sa.Time(), nullable=False),
            sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.String(length=10), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    ensure_index(inspector, "booking_slots", op.f("ix_booking_slots_id"), ["id"])
    ensure_index(inspector, "booking_slots", op.f("ix_booking_slots_therapy_name"), ["therapy_name"])
    ensure_index(inspector, "booking_slots", op.f("ix_booking_slots_booking_date"), ["booking_date"])

    if "therapy_bookings" not in inspector.get_table_names():
        op.create_table(
            "therapy_bookings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("reference_code", sa.String(length=32), nullable=False),
            sa.Column("cancel_token", sa.String(length=64), nullable=False),
            sa.Column("therapy_name", sa.String(length=255), nullable=False),
            sa.Column("customer_name", sa.String(length=255), nullable=False),
            sa.Column("phone", sa.String(length=50), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("booking_date", sa.Date(), nullable=False),
            sa.Column("slot_id", sa.Integer(), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=False),
            sa.Column("end_time", sa.Time(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("cancellation_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("reference_code", name="uq_therapy_bookings_reference_code"),
            sa.UniqueConstraint("cancel_token", name="uq_therapy_bookings_cancel_token"),
        )
    ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_id"), ["id"])
    ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_reference_code"), ["reference_code"])
    ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_cancel_token"), ["cancel_token"])
    ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_therapy_name"), ["therapy_name"])
    ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_email"), ["email"])
    ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_booking_date"), ["booking_date"])
    ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_slot_id"), ["slot_id"])
    ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_status"), ["status"])
    ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_created_at"), ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_therapy_bookings_created_at"), table_name="therapy_bookings")
    op.drop_index(op.f("ix_therapy_bookings_status"), table_name="therapy_bookings")
    op.drop_index(op.f("ix_therapy_bookings_slot_id"), table_name="therapy_bookings")
    op.drop_index(op.f("ix_therapy_bookings_booking_date"), table_name="therapy_bookings")
    op.drop_index(op.f("ix_therapy_bookings_email"), table_name="therapy_bookings")
    op.drop_index(op.f("ix_therapy_bookings_therapy_name"), table_name="therapy_bookings")
    op.drop_index(op.f("ix_therapy_bookings_cancel_token"), table_name="therapy_bookings")
    op.drop_index(op.f("ix_therapy_bookings_reference_code"), table_name="therapy_bookings")
    op.drop_index(op.f("ix_therapy_bookings_id"), table_name="therapy_bookings")
    op.drop_table("therapy_bookings")

    op.drop_index(op.f("ix_booking_slots_booking_date"), table_name="booking_slots")
    op.drop_index(op.f("ix_booking_slots_therapy_name"), table_name="booking_slots")
    op.drop_index(op.f("ix_booking_slots_id"), table_name="booking_slots")
    op.drop_table("booking_slots")
