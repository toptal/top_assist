"""Remove `bookmark` reaction feature

Revision ID: e2053a546a43
Revises: 6d6a7ca37e75
Create Date: 2024-07-02 18:42:37.339968

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2053a546a43"
down_revision: str | None = "6d6a7ca37e75"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_bookmarked_conversations_thread_id", table_name="bookmarked_conversations")
    op.drop_table("bookmarked_conversations")


def downgrade() -> None:
    op.create_table(
        "bookmarked_conversations",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("title", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("body", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("thread_id", sa.VARCHAR(length=17), autoincrement=False, nullable=False),
        sa.Column("bookmarked_on_slack", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column("posted_on_confluence", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column("page_id", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="bookmarked_conversations_pkey"),
    )
    op.create_index("ix_bookmarked_conversations_thread_id", "bookmarked_conversations", ["thread_id"], unique=False)
