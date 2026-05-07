"""normalize booking reference codes to booking ids

Revision ID: 20260507_09
Revises: 20260507_08
Create Date: 2026-05-07 18:20:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260507_09"
down_revision: Union[str, Sequence[str], None] = "20260507_08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "therapy_bookings" not in inspector.get_table_names():
        return

    op.execute(
        sa.text(
            """
            UPDATE therapy_bookings
            SET reference_code = CONCAT('SSW-', LPAD(id, 6, '0'))
            """
        )
    )


def downgrade() -> None:
    # Cannot safely restore previous random reference codes.
    pass
