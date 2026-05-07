"""add booking email logs

Revision ID: 20260507_12
Revises: 20260507_11
Create Date: 2026-05-07 22:10:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260507_12"
down_revision: Union[str, Sequence[str], None] = "20260507_11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "booking_email_logs" in inspector.get_table_names():
        return

    op.create_table(
        "booking_email_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("audience", sa.String(length=32), nullable=False),
        sa.Column("event_key", sa.String(length=100), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("delivery_status", sa.String(length=32), nullable=False, server_default="sent"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_booking_email_logs_id", "booking_email_logs", ["id"], unique=False)
    op.create_index("ix_booking_email_logs_booking_id", "booking_email_logs", ["booking_id"], unique=False)
    op.create_index("ix_booking_email_logs_audience", "booking_email_logs", ["audience"], unique=False)
    op.create_index("ix_booking_email_logs_event_key", "booking_email_logs", ["event_key"], unique=False)
    op.create_index("ix_booking_email_logs_recipient_email", "booking_email_logs", ["recipient_email"], unique=False)
    op.create_index("ix_booking_email_logs_delivery_status", "booking_email_logs", ["delivery_status"], unique=False)
    op.create_index("ix_booking_email_logs_created_at", "booking_email_logs", ["created_at"], unique=False)
    op.alter_column("booking_email_logs", "delivery_status", existing_type=sa.String(length=32), server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "booking_email_logs" not in inspector.get_table_names():
        return

    for index_name in [
        "ix_booking_email_logs_created_at",
        "ix_booking_email_logs_delivery_status",
        "ix_booking_email_logs_recipient_email",
        "ix_booking_email_logs_event_key",
        "ix_booking_email_logs_audience",
        "ix_booking_email_logs_booking_id",
        "ix_booking_email_logs_id",
    ]:
        op.drop_index(index_name, table_name="booking_email_logs")
    op.drop_table("booking_email_logs")
