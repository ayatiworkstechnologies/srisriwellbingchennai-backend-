"""add email notification settings

Revision ID: 20260511_13
Revises: 20260507_12
Create Date: 2026-05-11 11:45:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260511_13"
down_revision: Union[str, Sequence[str], None] = "20260507_12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "email_notification_settings" not in inspector.get_table_names():
        op.create_table(
            "email_notification_settings",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("booking_to_emails", sa.Text(), nullable=False),
            sa.Column("booking_cc_emails", sa.Text(), nullable=False),
            sa.Column("booking_bcc_emails", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_email_notification_settings_id", "email_notification_settings", ["id"], unique=False)
        op.create_index("ix_email_notification_settings_created_at", "email_notification_settings", ["created_at"], unique=False)
    existing = bind.execute(sa.text("SELECT COUNT(*) FROM email_notification_settings")).scalar() or 0
    if existing == 0:
        bind.execute(
            sa.text(
                "INSERT INTO email_notification_settings "
                "(id, booking_to_emails, booking_cc_emails, booking_bcc_emails, updated_at, created_at) "
                "VALUES (1, 'admin@srisriwellbeingchennai.com', '', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "email_notification_settings" not in inspector.get_table_names():
        return

    op.drop_index("ix_email_notification_settings_created_at", table_name="email_notification_settings")
    op.drop_index("ix_email_notification_settings_id", table_name="email_notification_settings")
    op.drop_table("email_notification_settings")
