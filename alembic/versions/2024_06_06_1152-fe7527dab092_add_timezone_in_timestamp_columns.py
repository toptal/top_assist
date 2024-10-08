"""Add timezone in Timestamp columns

Revision ID: fe7527dab092
Revises: 404e15433f31
Create Date: 2024-06-06 11:52:00.209509

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fe7527dab092"
down_revision: str | None = "404e15433f31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
tables: dict[str, list[str]] = {
    "user_feedback_scores": ["created_at", "updated_at"],
    "page_data": ["created_at", "updated_at", "created_date", "last_updated"],
    "user_scores": ["created_at", "updated_at"],
    "spaces": ["created_at", "updated_at", "last_import_date"],
    "qa_interactions": [
        "embedded_at",
        "answer_posted_on_slack",
        "question_timestamp",
        "answer_timestamp",
        "created_at",
        "updated_at",
    ],
    "channels": ["created_at", "updated_at"],
    "bookmarked_conversations": ["bookmarked_on_slack", "posted_on_confluence", "created_at", "updated_at"],
    "quiz_questions": ["posted_on_slack", "checked_on_slack", "posted_on_confluence", "created_at", "updated_at"],
    "service_cooldowns": ["created_at", "updated_at"],
}


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    for table, columns in tables.items():
        for column in columns:
            op.alter_column(table_name=table, column_name=column, type_=sa.DateTime(timezone=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    for table, columns in tables.items():
        for column in columns:
            op.alter_column(table_name=table, column_name=column, type_=sa.DateTime())

    # ### end Alembic commands ###
