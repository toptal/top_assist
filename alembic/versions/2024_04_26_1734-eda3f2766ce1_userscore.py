"""UserScore

Revision ID: eda3f2766ce1
Revises: 4fd21f3125fc
Create Date: 2024-04-26 17:34:01.162287

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eda3f2766ce1"
down_revision: str | None = "4fd21f3125fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slack_user_id", sa.String(), nullable=False),
        sa.Column("seeker_score", sa.Integer(), nullable=False),
        sa.Column("revealer_score", sa.Integer(), nullable=False),
        sa.Column("luminary_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slack_user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_scores")
