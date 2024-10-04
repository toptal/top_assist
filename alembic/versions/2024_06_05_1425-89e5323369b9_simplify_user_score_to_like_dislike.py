"""Simplify user score to like/dislike

Revision ID: 89e5323369b9
Revises: d04f3391155d
Create Date: 2024-06-05 14:25:56.557055

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "89e5323369b9"
down_revision: str | None = "d04f3391155d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user_feedback_scores", sa.Column("positive", sa.Boolean(), nullable=True))
    op.execute("UPDATE user_feedback_scores SET positive = score > 2")
    op.alter_column("user_feedback_scores", "positive", nullable=False)

    op.drop_column("user_feedback_scores", "score")


def downgrade() -> None:
    op.add_column("user_feedback_scores", sa.Column("score", sa.INTEGER(), autoincrement=False, nullable=True))
    op.execute("UPDATE user_feedback_scores SET score = CASE WHEN positive THEN 5 ELSE 1 END")
    op.alter_column("user_feedback_scores", "score", nullable=False)

    op.drop_column("user_feedback_scores", "positive")
