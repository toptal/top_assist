"""QuizQuestion

Revision ID: 7d601a62ec0e
Revises: 972428018c97
Create Date: 2024-04-26 17:27:15.177539

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d601a62ec0e"
down_revision: str | None = "972428018c97"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.String(), nullable=False),
        sa.Column("thread_id", sa.String(length=17), nullable=True),
        sa.Column("posted_on_slack", sa.DateTime(), nullable=True),
        sa.Column("posted_on_confluence", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_quiz_questions_thread_id",
        "quiz_questions",
        ["thread_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_quiz_questions_thread_id", table_name="quiz_questions")
    op.drop_table("quiz_questions")
