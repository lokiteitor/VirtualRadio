"""Per-station episode script settings.

Revision ID: 0002_station_episode_settings
Revises: 0001_initial
Create Date: 2026-06-16

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_station_episode_settings"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

UUIDV7 = sa.text("uuidv7()")
NOW = sa.text("now()")


def upgrade():
    op.create_table(
        "station_episode_settings",
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
        sa.Column("song_count", sa.SmallInteger(), server_default=sa.text("3"), nullable=False),
        sa.Column("news_count", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("commercial_count", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("caller_count", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("memories_per_caller", sa.SmallInteger(), server_default=sa.text("3"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("station_id", name="uq_episode_settings_station"),
        sa.CheckConstraint("song_count BETWEEN 0 AND 10", name="ck_episode_settings_song_count"),
        sa.CheckConstraint("news_count BETWEEN 0 AND 5", name="ck_episode_settings_news_count"),
        sa.CheckConstraint("commercial_count BETWEEN 0 AND 5", name="ck_episode_settings_commercial_count"),
        sa.CheckConstraint("caller_count BETWEEN 0 AND 5", name="ck_episode_settings_caller_count"),
        sa.CheckConstraint("memories_per_caller BETWEEN 0 AND 10", name="ck_episode_settings_memories"),
    )
    op.create_index(
        "ix_station_episode_settings_owner_id", "station_episode_settings", ["owner_id"]
    )


def downgrade():
    op.drop_table("station_episode_settings")
