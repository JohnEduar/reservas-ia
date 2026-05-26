"""availability engine: accommodation_availability and seasonal_prices tables

Revision ID: d7e8f9a0b1c2
Revises: b5c6d7e8f9a0
Create Date: 2026-05-25 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, None] = "b5c6d7e8f9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accommodation_availability",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("accommodation_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["accommodation_id"], ["accommodations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "accommodation_id", "date", name="uq_availability_acc_date"
        ),
    )
    op.create_index(
        op.f("ix_accommodation_availability_id"),
        "accommodation_availability",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_accommodation_availability_accommodation_id"),
        "accommodation_availability",
        ["accommodation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_accommodation_availability_date"),
        "accommodation_availability",
        ["date"],
        unique=False,
    )

    op.create_table(
        "seasonal_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("accommodation_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("price_per_night", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["accommodation_id"], ["accommodations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_seasonal_prices_id"), "seasonal_prices", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_seasonal_prices_accommodation_id"),
        "seasonal_prices",
        ["accommodation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_seasonal_prices_accommodation_id"), table_name="seasonal_prices"
    )
    op.drop_index(op.f("ix_seasonal_prices_id"), table_name="seasonal_prices")
    op.drop_table("seasonal_prices")

    op.drop_index(
        op.f("ix_accommodation_availability_date"),
        table_name="accommodation_availability",
    )
    op.drop_index(
        op.f("ix_accommodation_availability_accommodation_id"),
        table_name="accommodation_availability",
    )
    op.drop_index(
        op.f("ix_accommodation_availability_id"),
        table_name="accommodation_availability",
    )
    op.drop_table("accommodation_availability")
