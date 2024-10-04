"""Remove gamification feature

Revision ID: 6d6a7ca37e75
Revises: 26fa7f71ffe6
Create Date: 2024-07-02 18:07:13.323147

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6d6a7ca37e75"
down_revision: str | None = "26fa7f71ffe6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("user_scores")
    op.drop_column("quiz_questions", "slack_user_ids_awarded")


def downgrade() -> None:
    op.add_column(
        "quiz_questions",
        sa.Column("slack_user_ids_awarded", postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
    )
    op.create_table(
        "user_scores",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("slack_user_id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("seeker_score", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("revealer_score", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("luminary_score", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="user_scores_pkey"),
        sa.UniqueConstraint("slack_user_id", name="user_scores_slack_user_id_key"),
    )
