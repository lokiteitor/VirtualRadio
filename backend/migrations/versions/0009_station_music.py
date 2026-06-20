"""Per-station music selection (whitelist of tracks a station may play).

Revision ID: 0009_station_music
Revises: 0008_generation_traces
Create Date: 2026-06-19

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0009_station_music"
down_revision = "0008_generation_traces"
branch_labels = None
depends_on = None

UUIDV7 = sa.text("uuidv7()")
NOW = sa.text("now()")


def upgrade():
    op.create_table(
        "station_music",
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
            "music_track_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("music_tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("station_id", "music_track_id", name="uq_station_music"),
    )
    op.create_index("ix_station_music_owner_id", "station_music", ["owner_id"])
    op.create_index("ix_station_music_station_id", "station_music", ["station_id"])
    op.create_index("ix_station_music_music_track_id", "station_music", ["music_track_id"])


def downgrade():
    op.drop_table("station_music")
