"""seed alternative treatments

Revision ID: 20260514_19
Revises: 20260514_18
Create Date: 2026-05-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260514_19"
down_revision: Union[str, None] = "20260514_18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TREATMENTS = [
    ("osteopathy", "Osteopathy", "A drug-free, non-invasive manual therapy that aims to improve health across all body systems by manipulating and strengthening the musculoskeletal framework.", "/images/heal/osteopathy.png", 1),
    ("ozone", "Ozone Therapy", "A medical therapy that uses ozone gas to treat infections, wounds, and multiple diseases by inactivating bacteria, viruses, fungi, yeast, and protozoa.", "/images/heal/ozone.png", 2),
    ("meru-chikitsa", "Meru Chikitsa", "An ancient Ayurvedic spinal therapy involving specific manipulations of the vertebral column to realign the spine and restore the flow of prana through the body.", "/images/heal/meru.png", 3),
    ("rakkenho", "Rakkenho", "A Japanese holistic healing system based on the correction of energy flow through the body's meridians, promoting natural self-healing and deep relaxation.", "/images/heal/rakkenho.png", 4),
    ("lb-therapy", "L&B Therapy", "A transformative bodywork modality that integrates breath, movement, and touch to release deep-seated physical and emotional patterns held in the body.", "/images/heal/l&b.png", 5),
    ("lymphatic", "Manual Lymphatic Drainage", "A gentle rhythmic massage technique that stimulates the lymphatic system to drain excess fluid, reduce swelling, and support the body's natural detoxification process.", "/images/heal/manual.png", 6),
    ("marma", "Marma Chikitsa", "Marma Chikitsa involves the stimulation of vital energy points on the body to activate the body's innate healing intelligence and restore the flow of prana.", "/images/heal/marma.png", 7),
    ("reflexology", "Reflexology", "A therapeutic method based on the principle that there are reflexes in the feet, hands, and ears that correspond to every part, organ, and gland in the body.", "/images/heal/reflexology.png", 8),
    ("light-sound", "Light & Sound Therapy", "An innovative therapy that uses specific frequencies of light and sound to synchronise brain waves, reduce stress, and support mental and emotional wellness.", "/images/heal/light.png", 9),
]


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "content_categories" in inspector.get_table_names():
        existing = connection.execute(
            sa.text("SELECT id FROM content_categories WHERE slug = :slug"),
            {"slug": "alternative"},
        ).first()
        if not existing:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO content_categories
                        (slug, label, description, sort_order, is_active, created_at)
                    VALUES
                        (:slug, :label, :description, :sort_order, :is_active, CURRENT_TIMESTAMP)
                    """
                ),
                {
                    "slug": "alternative",
                    "label": "Alternative",
                    "description": "Alternative and integrative therapy content.",
                    "sort_order": 4,
                    "is_active": "true",
                },
            )

    if "alternative_treatments" not in inspector.get_table_names():
        return

    for item_id, name, short_desc, image, sort_order in TREATMENTS:
        existing = connection.execute(
            sa.text("SELECT id FROM alternative_treatments WHERE item_id = :item_id"),
            {"item_id": item_id},
        ).first()
        values = {
            "item_id": item_id,
            "name": name,
            "category": "alternative",
            "short_desc": short_desc,
            "image": image,
            "sort_order": sort_order,
            "is_active": "true",
        }
        if existing:
            connection.execute(
                sa.text(
                    """
                    UPDATE alternative_treatments
                    SET name = :name,
                        category = :category,
                        short_desc = :short_desc,
                        image = :image,
                        sort_order = :sort_order,
                        is_active = :is_active
                    WHERE item_id = :item_id
                    """
                ),
                values,
            )
        else:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO alternative_treatments
                        (item_id, name, category, short_desc, image, sort_order, is_active, created_at)
                    VALUES
                        (:item_id, :name, :category, :short_desc, :image, :sort_order, :is_active, CURRENT_TIMESTAMP)
                    """
                ),
                values,
            )


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "alternative_treatments" in inspector.get_table_names():
        connection.execute(
            sa.text("DELETE FROM alternative_treatments WHERE item_id IN :item_ids").bindparams(
                sa.bindparam("item_ids", expanding=True)
            ),
            {"item_ids": [item[0] for item in TREATMENTS]},
        )

    if "content_categories" in inspector.get_table_names():
        connection.execute(
            sa.text("DELETE FROM content_categories WHERE slug = :slug"),
            {"slug": "alternative"},
        )
