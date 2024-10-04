"""QAInteraction

Revision ID: 0b28658a6173
Revises: 7d601a62ec0e
Create Date: 2024-04-26 17:28:15.575432

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0b28658a6173"
down_revision: str | None = "7d601a62ec0e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "qa_interactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.String(), nullable=False),
        sa.Column("thread_id", sa.String(length=17), nullable=False),
        sa.Column("assistant_thread_id", sa.String(), nullable=False),
        sa.Column("answer_text", sa.String(), nullable=False),
        sa.Column("channel_id", sa.String(), nullable=False),
        sa.Column("slack_user_id", sa.String(), nullable=False),
        sa.Column("question_timestamp", sa.DateTime(), nullable=False),
        sa.Column("answer_timestamp", sa.DateTime(), nullable=False),
        sa.Column("comments", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_qa_interactions_thread_id"),
        "qa_interactions",
        ["thread_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_qa_interactions_thread_id"), table_name="qa_interactions")
    op.drop_table("qa_interactions")
