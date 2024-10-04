"""Remove knowledge gap feature

Revision ID: c4a3831f57ef
Revises: e2053a546a43
Create Date: 2024-07-02 19:13:11.706188

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4a3831f57ef"
down_revision: str | None = "e2053a546a43"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_quiz_questions_thread_id", table_name="quiz_questions")
    op.drop_table("quiz_questions")


def downgrade() -> None:
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("question_text", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("thread_id", sa.VARCHAR(length=17), autoincrement=False, nullable=True),
        sa.Column("posted_on_slack", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column("posted_on_confluence", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column("page_id", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("checked_on_slack", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="quiz_questions_pkey"),
    )
    op.create_index("ix_quiz_questions_thread_id", "quiz_questions", ["thread_id"], unique=False)
