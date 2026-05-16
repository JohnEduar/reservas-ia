"""accommodations module

Revision ID: b5c6d7e8f9a0
Revises: 1b00598c3491
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, None] = "1b00598c3491"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "amenities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_amenities_id"), "amenities", ["id"], unique=False)

    op.create_table(
        "accommodations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("price_per_night", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("max_guests", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_accommodations_id"), "accommodations", ["id"], unique=False)
    op.create_index(op.f("ix_accommodations_location"), "accommodations", ["location"], unique=False)
    op.create_index(op.f("ix_accommodations_owner_id"), "accommodations", ["owner_id"], unique=False)

    op.create_table(
        "accommodation_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("accommodation_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["accommodation_id"], ["accommodations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_accommodation_images_id"), "accommodation_images", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_accommodation_images_accommodation_id"),
        "accommodation_images",
        ["accommodation_id"],
        unique=False,
    )

    op.create_table(
        "accommodation_amenities",
        sa.Column("accommodation_id", sa.Integer(), nullable=False),
        sa.Column("amenity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["accommodation_id"], ["accommodations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["amenity_id"], ["amenities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("accommodation_id", "amenity_id"),
    )


def downgrade() -> None:
    op.drop_table("accommodation_amenities")
    op.drop_index(op.f("ix_accommodation_images_accommodation_id"), table_name="accommodation_images")
    op.drop_index(op.f("ix_accommodation_images_id"), table_name="accommodation_images")
    op.drop_table("accommodation_images")
    op.drop_index(op.f("ix_accommodations_owner_id"), table_name="accommodations")
    op.drop_index(op.f("ix_accommodations_location"), table_name="accommodations")
    op.drop_index(op.f("ix_accommodations_id"), table_name="accommodations")
    op.drop_table("accommodations")
    op.drop_index(op.f("ix_amenities_id"), table_name="amenities")
    op.drop_table("amenities")
