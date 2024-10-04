"""BookmarkedConversation

Revision ID: 972428018c97
Revises: 04dc5d59ccc1
Create Date: 2024-04-26 17:25:06.567941

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "972428018c97"
down_revision: str | None = "04dc5d59ccc1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bookmarked_conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("thread_id", sa.String(length=17), nullable=False),
        sa.Column("bookmarked_on_slack", sa.DateTime(), nullable=False),
        sa.Column("posted_on_confluence", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bookmarked_conversations_thread_id",
        "bookmarked_conversations",
        ["thread_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_bookmarked_conversations_thread_id",
        table_name="bookmarked_conversations",
    )
    op.drop_table("bookmarked_conversations")
