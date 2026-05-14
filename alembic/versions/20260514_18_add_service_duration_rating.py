"""add service duration and rating

Revision ID: 20260514_18
Revises: 20260514_17
Create Date: 2026-05-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260514_18"
down_revision: Union[str, None] = "20260514_17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_RATINGS = {
    "Nadi Pariksha": 4.9,
    "Panchakarma Rituals": 4.9,
    "Marma Chikitsa": 4.8,
    "Osteopathic Therapy": 4.8,
    "Ozone Therapy": 4.7,
    "Meru Therapy": 4.8,
    "Craniosacral Therapy": 4.8,
    "Pain Management Therapies": 4.9,
}


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "services" not in inspector.get_table_names():
        return

    service_columns = {column["name"] for column in inspector.get_columns("services")}
    if "duration" not in service_columns:
        op.add_column(
            "services",
            sa.Column("duration", sa.String(length=50), nullable=False, server_default=""),
        )
    if "rating" not in service_columns:
        op.add_column("services", sa.Column("rating", sa.Float(), nullable=True))

    if "relaxation_therapies" in inspector.get_table_names():
        therapy_durations = connection.execute(
            sa.text("SELECT title, duration FROM relaxation_therapies")
        ).all()
        for title, duration in therapy_durations:
            connection.execute(
                sa.text(
                    """
                    UPDATE services
                    SET duration = :duration
                    WHERE title = :title AND (duration IS NULL OR duration = '')
                    """
                ),
                {"title": title, "duration": duration or ""},
            )

    for title, rating in DEFAULT_RATINGS.items():
        connection.execute(
            sa.text(
                "UPDATE services SET rating = :rating WHERE title = :title AND rating IS NULL"
            ),
            {"title": title, "rating": rating},
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    if "services" not in inspector.get_table_names():
        return

    service_columns = {column["name"] for column in inspector.get_columns("services")}
    if "rating" in service_columns:
        op.drop_column("services", "rating")
    if "duration" in service_columns:
        op.drop_column("services", "duration")
