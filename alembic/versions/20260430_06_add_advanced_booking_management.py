"""add advanced booking management

Revision ID: 20260430_06
Revises: 20260430_05
Create Date: 2026-04-30 23:55:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260430_06"
down_revision: Union[str, Sequence[str], None] = "20260430_05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def ensure_index(inspector, table_name: str, index_name: str, columns: list[str], unique: bool = False) -> None:
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in existing_indexes:
        op.create_index(index_name, table_name, columns, unique=unique)


def has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "therapists" not in inspector.get_table_names():
        op.create_table(
            "therapists",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("phone", sa.String(length=50), nullable=False),
            sa.Column("specialties", sa.Text(), nullable=False),
            sa.Column("bio", sa.Text(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email", name="uq_therapists_email"),
        )
    ensure_index(inspector, "therapists", op.f("ix_therapists_id"), ["id"])
    ensure_index(inspector, "therapists", op.f("ix_therapists_full_name"), ["full_name"])
    ensure_index(inspector, "therapists", op.f("ix_therapists_email"), ["email"])

    if "therapist_availabilities" not in inspector.get_table_names():
        op.create_table(
            "therapist_availabilities",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("therapist_id", sa.Integer(), nullable=False),
            sa.Column("therapy_name", sa.String(length=255), nullable=False),
            sa.Column("day_of_week", sa.Integer(), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=False),
            sa.Column("end_time", sa.Time(), nullable=False),
            sa.Column("slot_interval_minutes", sa.Integer(), nullable=False, server_default="45"),
            sa.Column("max_bookings_per_slot", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.String(length=10), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    ensure_index(inspector, "therapist_availabilities", op.f("ix_therapist_availabilities_id"), ["id"])
    ensure_index(inspector, "therapist_availabilities", op.f("ix_therapist_availabilities_therapist_id"), ["therapist_id"])
    ensure_index(inspector, "therapist_availabilities", op.f("ix_therapist_availabilities_therapy_name"), ["therapy_name"])
    ensure_index(inspector, "therapist_availabilities", op.f("ix_therapist_availabilities_day_of_week"), ["day_of_week"])

    if "therapist_blackouts" not in inspector.get_table_names():
        op.create_table(
            "therapist_blackouts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("therapist_id", sa.Integer(), nullable=False),
            sa.Column("blackout_date", sa.Date(), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=True),
            sa.Column("end_time", sa.Time(), nullable=True),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    ensure_index(inspector, "therapist_blackouts", op.f("ix_therapist_blackouts_id"), ["id"])
    ensure_index(inspector, "therapist_blackouts", op.f("ix_therapist_blackouts_therapist_id"), ["therapist_id"])
    ensure_index(inspector, "therapist_blackouts", op.f("ix_therapist_blackouts_blackout_date"), ["blackout_date"])

    if "therapy_bookings" in inspector.get_table_names():
        if not has_column(inspector, "therapy_bookings", "therapist_id"):
            op.add_column("therapy_bookings", sa.Column("therapist_id", sa.Integer(), nullable=True))
        if not has_column(inspector, "therapy_bookings", "therapist_name"):
            op.add_column("therapy_bookings", sa.Column("therapist_name", sa.String(length=255), nullable=True))
        ensure_index(inspector, "therapy_bookings", op.f("ix_therapy_bookings_therapist_id"), ["therapist_id"])


def downgrade() -> None:
    inspector = inspect(op.get_bind())

    if "therapy_bookings" in inspector.get_table_names():
        if "ix_therapy_bookings_therapist_id" in {index["name"] for index in inspector.get_indexes("therapy_bookings")}:
            op.drop_index(op.f("ix_therapy_bookings_therapist_id"), table_name="therapy_bookings")
        if has_column(inspector, "therapy_bookings", "therapist_name"):
            op.drop_column("therapy_bookings", "therapist_name")
        if has_column(inspector, "therapy_bookings", "therapist_id"):
            op.drop_column("therapy_bookings", "therapist_id")

    op.drop_index(op.f("ix_therapist_blackouts_blackout_date"), table_name="therapist_blackouts")
    op.drop_index(op.f("ix_therapist_blackouts_therapist_id"), table_name="therapist_blackouts")
    op.drop_index(op.f("ix_therapist_blackouts_id"), table_name="therapist_blackouts")
    op.drop_table("therapist_blackouts")

    op.drop_index(op.f("ix_therapist_availabilities_day_of_week"), table_name="therapist_availabilities")
    op.drop_index(op.f("ix_therapist_availabilities_therapy_name"), table_name="therapist_availabilities")
    op.drop_index(op.f("ix_therapist_availabilities_therapist_id"), table_name="therapist_availabilities")
    op.drop_index(op.f("ix_therapist_availabilities_id"), table_name="therapist_availabilities")
    op.drop_table("therapist_availabilities")

    op.drop_index(op.f("ix_therapists_email"), table_name="therapists")
    op.drop_index(op.f("ix_therapists_full_name"), table_name="therapists")
    op.drop_index(op.f("ix_therapists_id"), table_name="therapists")
    op.drop_table("therapists")
