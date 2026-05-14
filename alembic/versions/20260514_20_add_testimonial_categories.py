"""add testimonial categories

Revision ID: 20260514_20
Revises: 20260514_19
Create Date: 2026-05-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260514_20"
down_revision: Union[str, None] = "20260514_19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TESTIMONIALS = [
    ("home", "Anusha Rajan", "A deeply soothing and authentic experience. Netra Tejas felt gentle yet remarkably effective, bringing clarity and comfort in the most natural way. A refined approach to non-invasive care that truly delivers.", 1),
    ("home", "Muthukrishnan Gopal", "An exceptional destination for authentic Ayurvedic care. The experience is thoughtfully curated, offering both depth and genuine healing in a calm, welcoming environment.", 2),
    ("home", "Meera Venkatesh", "What stood out was the level of personalisation. Beginning with Nadi Pariksha, every therapy felt aligned to my body's needs. The experience was unhurried, intuitive, and deeply restorative.", 3),
    ("home", "Rohit Subramanian", "From Abhyanga to relaxation therapies, each session brought a noticeable sense of lightness and ease. The care extended to every member of the family, making it a truly holistic experience.", 4),
    ("relax", "Priya S.", "The Nadi Pariksha consultation was eye-opening. The doctors accurately pinpointed my digestive issues and the tailored Ayurvedic diet transformed my health within weeks.", 1),
    ("relax", "Ramesh K.", "I've been to many spas and wellness centers, but the authenticity and serene ambiance here is unmatched. The stress relief therapies are truly a lifesaver for my corporate lifestyle.", 2),
    ("relax", "Anita M.", "Exceptional care and truly personalized treatments. The staff goes above and beyond to make you feel comfortable and understood. Highly recommend for chronic joint pain.", 3),
    ("nadi", "Ruban Kumar", "The Nadi Pariksha experience I had at Sri Sri Wellbeing was the best thing I've done for my health. The doctor immediately identified my issues and I got a customised set of treatments and supplements from my visits.", 1),
    ("nadi", "Priya Sharma", "I was suffering from chronic digestive issues for years. The Nadi Vaidya accurately identified the root cause through pulse diagnosis and recommended a personalised treatment plan.", 2),
    ("nadi", "Arjun Menon", "As someone dealing with stress-related health problems, Nadi Pariksha was a revelation. The Ayurvedic treatments and lifestyle changes suggested have transformed my sleep quality and mental clarity.", 3),
    ("netra", "Anusha Rajan", "Netra Tejas felt gentle yet remarkably effective, bringing clarity and comfort in the most natural way.", 1),
    ("netra", "Muthukrishnan Gopal", "An exceptional destination for authentic Ayurvedic care with a calm, welcoming environment.", 2),
]


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "testimonials" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("testimonials")}
    if "category" not in columns:
        op.add_column(
            "testimonials",
            sa.Column("category", sa.String(length=50), nullable=False, server_default="home"),
        )
        op.create_index(op.f("ix_testimonials_category"), "testimonials", ["category"], unique=False)

    for category, name, review, sort_order in TESTIMONIALS:
        existing = connection.execute(
            sa.text("SELECT id FROM testimonials WHERE category = :category AND name = :name"),
            {"category": category, "name": name},
        ).first()
        values = {
            "category": category,
            "name": name,
            "review": review,
            "sort_order": sort_order,
            "is_active": "true",
        }
        if existing:
            connection.execute(
                sa.text(
                    """
                    UPDATE testimonials
                    SET review = :review,
                        sort_order = :sort_order,
                        is_active = :is_active
                    WHERE category = :category AND name = :name
                    """
                ),
                values,
            )
        else:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO testimonials
                        (category, name, review, sort_order, is_active, created_at)
                    VALUES
                        (:category, :name, :review, :sort_order, :is_active, CURRENT_TIMESTAMP)
                    """
                ),
                values,
            )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    if "testimonials" not in inspector.get_table_names():
        return

    indexes = {index["name"] for index in inspector.get_indexes("testimonials")}
    if op.f("ix_testimonials_category") in indexes:
        op.drop_index(op.f("ix_testimonials_category"), table_name="testimonials")

    columns = {column["name"] for column in inspector.get_columns("testimonials")}
    if "category" in columns:
        op.drop_column("testimonials", "category")
