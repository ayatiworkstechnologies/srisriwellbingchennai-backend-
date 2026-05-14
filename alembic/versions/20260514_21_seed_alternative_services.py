"""seed alternative services

Revision ID: 20260514_21
Revises: 20260514_20
Create Date: 2026-05-14 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260514_21"
down_revision = "20260514_20"
branch_labels = None
depends_on = None


RECORDS = [
    ("Osteopathy", "A drug-free, non-invasive manual therapy that aims to improve health across all body systems by manipulating and strengthening the musculoskeletal framework.", "/images/heal/osteopathy.png", 4.8, 1),
    ("Ozone Therapy", "A medical therapy that uses ozone gas to treat infections, wounds, and multiple diseases by inactivating bacteria, viruses, fungi, yeast, and protozoa.", "/images/heal/ozone.png", 4.7, 2),
    ("Meru Chikitsa", "An ancient Ayurvedic spinal therapy involving specific manipulations of the vertebral column to realign the spine and restore the flow of prana through the body.", "/images/heal/meru.png", 4.8, 3),
    ("Rakkenho", "A Japanese holistic healing system based on the correction of energy flow through the body's meridians, promoting natural self-healing and deep relaxation.", "/images/heal/rakkenho.png", 4.8, 4),
    ("L&B Therapy", "A transformative bodywork modality that integrates breath, movement, and touch to release deep-seated physical and emotional patterns held in the body.", "/images/heal/l&b.png", 4.8, 5),
    ("Manual Lymphatic Drainage", "A gentle rhythmic massage technique that stimulates the lymphatic system to drain excess fluid, reduce swelling, and support the body's natural detoxification process.", "/images/heal/manual.png", 4.8, 6),
    ("Marma Chikitsa", "Marma Chikitsa involves the stimulation of vital energy points on the body to activate the body's innate healing intelligence and restore the flow of prana.", "/images/heal/marma.png", 4.8, 7),
    ("Reflexology", "A therapeutic method based on the principle that there are reflexes in the feet, hands, and ears that correspond to every part, organ, and gland in the body.", "/images/heal/reflexology.png", 4.8, 8),
    ("Light & Sound Therapy", "An innovative therapy that uses specific frequencies of light and sound to synchronise brain waves, reduce stress, and support mental and emotional wellness.", "/images/heal/light.png", 4.7, 9),
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "services" not in inspector.get_table_names():
        return

    for title, description, image, rating, sort_order in RECORDS:
        existing = bind.execute(
            sa.text("SELECT id FROM services WHERE category = 'alternative' AND title = :title"),
            {"title": title},
        ).scalar()

        values = {
            "category": "alternative",
            "title": title,
            "short_description": description,
            "description": description,
            "benefits": "Holistic care support\nPersonalized wellness approach\nNon-invasive therapeutic support",
            "image": image,
            "duration": "",
            "rating": rating,
            "sort_order": sort_order,
            "is_active": "true",
        }

        if existing:
            bind.execute(
                sa.text(
                    """
                    UPDATE services
                    SET short_description = :short_description,
                        description = :description,
                        image = :image,
                        duration = :duration,
                        rating = :rating,
                        sort_order = :sort_order,
                        is_active = :is_active
                    WHERE id = :id
                    """
                ),
                {**values, "id": existing},
            )
        else:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO services
                    (category, title, short_description, description, benefits, image, duration, rating, sort_order, is_active, created_at)
                    VALUES
                    (:category, :title, :short_description, :description, :benefits, :image, :duration, :rating, :sort_order, :is_active, CURRENT_TIMESTAMP)
                    """
                ),
                values,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "services" not in inspector.get_table_names():
        return

    bind.execute(
        sa.text("DELETE FROM services WHERE category = 'alternative' AND title IN :titles").bindparams(
            sa.bindparam("titles", expanding=True)
        ),
        {"titles": [record[0] for record in RECORDS]},
    )
