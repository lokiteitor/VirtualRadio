"""Per-station news-read ledger (read news once per station).

Revision ID: 0007_station_news_reads
Revises: 0006_tts_voices
Create Date: 2026-06-19

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007_station_news_reads"
down_revision = "0006_tts_voices"
branch_labels = None
depends_on = None

UUIDV7 = sa.text("uuidv7()")
NOW = sa.text("now()")


def upgrade():
    op.create_table(
        "station_news_reads",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=UUIDV7, nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "station_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "news_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("news_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "episode_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("episodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("station_id", "news_item_id", name="uq_station_news_read"),
    )
    op.create_index("ix_station_news_reads_owner_id", "station_news_reads", ["owner_id"])
    op.create_index("ix_station_news_reads_station_id", "station_news_reads", ["station_id"])
    op.create_index("ix_station_news_reads_news_item_id", "station_news_reads", ["news_item_id"])


def downgrade():
    op.drop_table("station_news_reads")
