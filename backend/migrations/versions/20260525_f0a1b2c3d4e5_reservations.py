"""reservation flow: reservations table

Revision ID: f0a1b2c3d4e5
Revises: d7e8f9a0b1c2
Create Date: 2026-05-25 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, None] = "d7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("accommodation_id", sa.Integer(), nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("guest_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("total_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["accommodation_id"], ["accommodations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["guest_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_reservations_id"), "reservations", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_reservations_accommodation_id"),
        "reservations",
        ["accommodation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reservations_guest_id"), "reservations", ["guest_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_reservations_guest_id"), table_name="reservations")
    op.drop_index(
        op.f("ix_reservations_accommodation_id"), table_name="reservations"
    )
    op.drop_index(op.f("ix_reservations_id"), table_name="reservations")
    op.drop_table("reservations")
