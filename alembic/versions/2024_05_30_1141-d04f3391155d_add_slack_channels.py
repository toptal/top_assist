"""Add Slack Channels

Revision ID: d04f3391155d
Revises: dc70c5e7f152
Create Date: 2024-05-30 11:41:17.609083

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d04f3391155d"
down_revision: str | None = "dc70c5e7f152"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "channels",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("slack_channel_id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="channels_pkey"),
        sa.UniqueConstraint("slack_channel_id"),
    )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("channels")
    # ### end Alembic commands ###
