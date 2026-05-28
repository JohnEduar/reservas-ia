"""reviews module

Revision ID: c9d1e2f3a4b5
Revises: b5c6d7e8f9a0
Create Date: 2026-05-28 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9d1e2f3a4b5"
down_revision: Union[str, None] = "b5c6d7e8f9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("accommodation_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["accommodation_id"], ["accommodations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reviewer_id", "accommodation_id", name="uq_review_user_accommodation"),
    )
    op.create_index(op.f("ix_reviews_id"), "reviews", ["id"], unique=False)
    op.create_index(op.f("ix_reviews_accommodation_id"), "reviews", ["accommodation_id"], unique=False)
    op.create_index(op.f("ix_reviews_reviewer_id"), "reviews", ["reviewer_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reviews_reviewer_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_accommodation_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_id"), table_name="reviews")
    op.drop_table("reviews")
