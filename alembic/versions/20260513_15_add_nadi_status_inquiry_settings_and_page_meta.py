"""add nadi status inquiry settings and page meta

Revision ID: 20260513_15
Revises: 20260513_14
Create Date: 2026-05-13 16:30:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260513_15"
down_revision: Union[str, Sequence[str], None] = "20260513_14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "nadi_camps" in inspector.get_table_names() and not _column_exists(inspector, "nadi_camps", "status"):
        op.add_column("nadi_camps", sa.Column("status", sa.String(length=32), nullable=False, server_default="active"))
        op.create_index("ix_nadi_camps_status", "nadi_camps", ["status"], unique=False)
        bind.execute(sa.text("UPDATE nadi_camps SET status = 'active' WHERE status IS NULL OR status = ''"))

    if "email_notification_settings" in inspector.get_table_names():
        text_columns = {
            "inquiry_to_emails": "",
            "inquiry_cc_emails": "",
            "inquiry_bcc_emails": "",
            "inquiry_auto_reply_message": (
                "Thank you for reaching Sri Sri Wellbeing Chennai. We have received your enquiry and our team will connect with you within the next 48 hours."
            ),
        }
        string_columns = {
            "inquiry_auto_reply_enabled": ("true", sa.String(length=10)),
            "inquiry_auto_reply_subject": (
                "Thank you for contacting Sri Sri Wellbeing Chennai",
                sa.String(length=255),
            ),
        }

        for column_name, default_value in text_columns.items():
            if not _column_exists(inspector, "email_notification_settings", column_name):
                op.add_column(
                    "email_notification_settings",
                    sa.Column(column_name, sa.Text(), nullable=True),
                )
                bind.execute(
                    sa.text(
                        f"UPDATE email_notification_settings SET {column_name} = :default_value "
                        f"WHERE {column_name} IS NULL"
                    ),
                    {"default_value": default_value},
                )
                op.alter_column(
                    "email_notification_settings",
                    column_name,
                    existing_type=sa.Text(),
                    nullable=False,
                )

        for column_name, (default_value, column_type) in string_columns.items():
            if not _column_exists(inspector, "email_notification_settings", column_name):
                op.add_column(
                    "email_notification_settings",
                    sa.Column(column_name, column_type, nullable=False, server_default=default_value),
                )

        bind.execute(
            sa.text(
                "UPDATE email_notification_settings "
                "SET inquiry_to_emails = booking_to_emails "
                "WHERE inquiry_to_emails IS NULL OR inquiry_to_emails = ''"
            )
        )

    if "page_meta_settings" not in inspector.get_table_names():
        op.create_table(
            "page_meta_settings",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("page_key", sa.String(length=100), nullable=False),
            sa.Column("page_path", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("is_active", sa.String(length=10), nullable=False, server_default="true"),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_page_meta_settings_id", "page_meta_settings", ["id"], unique=False)
        op.create_index("ix_page_meta_settings_page_key", "page_meta_settings", ["page_key"], unique=True)
        op.create_index("ix_page_meta_settings_page_path", "page_meta_settings", ["page_path"], unique=False)
        op.create_index("ix_page_meta_settings_created_at", "page_meta_settings", ["created_at"], unique=False)

        default_rows = [
            ("home", "/", "Sri Sri Wellbeing Chennai | Ayurveda, Panchakarma & Relaxation", "Discover natural healing at Sri Sri Wellbeing Chennai with Ayurvedic treatments, Panchakarma therapies, relaxation rituals, and personalised wellness care."),
            ("about", "/about-us", "About Sri Sri Wellbeing Chennai", "Learn about Sri Sri Wellbeing Chennai, our Ayurvedic approach, wellness philosophy, and personalised healing experience."),
            ("relax", "/relaxationtherapy", "Relaxation Therapy | Sri Sri Wellbeing Chennai", "Explore Ayurvedic relaxation therapies, renewal rituals, and restorative wellbeing experiences at Sri Sri Wellbeing Chennai."),
            ("facilities", "/facilities", "Facilities | Sri Sri Wellbeing Chennai", "Explore the facilities, stay options, therapy spaces, and wellness environment at Sri Sri Wellbeing Chennai."),
            ("products", "/products", "Products | Sri Sri Wellbeing Chennai", "Browse wellness products and supportive Ayurvedic offerings from Sri Sri Wellbeing Chennai."),
            ("contact", "/contact", "Contact Sri Sri Wellbeing Chennai", "Reach Sri Sri Wellbeing Chennai for Ayurveda treatments, Panchakarma therapies, wellness appointments, and enquiries."),
            ("nadi-pariksha", "/heal/nadi-pariksha", "Nadi Pariksha | Sri Sri Wellbeing Chennai", "Book Nadi Pariksha consultations and upcoming camps with expert Ayurvedic guidance at Sri Sri Wellbeing Chennai."),
            ("panchakarma", "/heal/panchakarma", "Panchakarma | Sri Sri Wellbeing Chennai", "Discover Panchakarma detox, cleansing therapies, and Ayurvedic renewal programmes at Sri Sri Wellbeing Chennai."),
            ("alternative-treatments", "/heal/alternativetreatments", "Alternative Treatments | Sri Sri Wellbeing Chennai", "Explore complementary Ayurvedic and holistic treatments offered at Sri Sri Wellbeing Chennai."),
            ("netra-tejas", "/heal/netratejas", "Netra Tejas | Sri Sri Wellbeing Chennai", "Learn about Netra Tejas and supportive eye-focused wellness therapies at Sri Sri Wellbeing Chennai."),
        ]
        for page_key, page_path, title, description in default_rows:
            bind.execute(
                sa.text(
                    "INSERT INTO page_meta_settings (page_key, page_path, title, description, is_active, updated_at, created_at) "
                    "VALUES (:page_key, :page_path, :title, :description, 'true', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {
                    "page_key": page_key,
                    "page_path": page_path,
                    "title": title,
                    "description": description,
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "page_meta_settings" in inspector.get_table_names():
        op.drop_index("ix_page_meta_settings_created_at", table_name="page_meta_settings")
        op.drop_index("ix_page_meta_settings_page_path", table_name="page_meta_settings")
        op.drop_index("ix_page_meta_settings_page_key", table_name="page_meta_settings")
        op.drop_index("ix_page_meta_settings_id", table_name="page_meta_settings")
        op.drop_table("page_meta_settings")

    if "email_notification_settings" in inspector.get_table_names():
        for column_name in [
            "inquiry_auto_reply_message",
            "inquiry_auto_reply_subject",
            "inquiry_auto_reply_enabled",
            "inquiry_bcc_emails",
            "inquiry_cc_emails",
            "inquiry_to_emails",
        ]:
            if _column_exists(inspector, "email_notification_settings", column_name):
                op.drop_column("email_notification_settings", column_name)

    if "nadi_camps" in inspector.get_table_names() and _column_exists(inspector, "nadi_camps", "status"):
        op.drop_index("ix_nadi_camps_status", table_name="nadi_camps")
        op.drop_column("nadi_camps", "status")
