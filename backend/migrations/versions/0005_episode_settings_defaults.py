"""Tune episode settings defaults for a radio-like block rhythm.

Raises the per-episode defaults so the new block structure (>= 3 songs back-to-back
per block, ad break after each block, callers spread across the show) is visible
out of the box: songs 3 -> 9 (three blocks of three), commercials 1 -> 2 (recycled
into each break), callers 1 -> 3 (one per block return). ``news_count`` stays at 1.

The ``server_default`` change only affects NEW rows; an ``UPDATE`` also migrates
rows still holding the exact legacy default tuple (song=3, news=1, commercial=1,
caller=1) so an already-seeded demo reflects the new rhythm. Rows the user
customised to any other values are left untouched.

Revision ID: 0005_episode_settings_defaults
Revises: 0004_settings_language
Create Date: 2026-06-16

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_episode_settings_defaults"
down_revision = "0004_settings_language"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("station_episode_settings", "song_count", server_default=sa.text("9"))
    op.alter_column("station_episode_settings", "commercial_count", server_default=sa.text("2"))
    op.alter_column("station_episode_settings", "caller_count", server_default=sa.text("3"))

    # Migrate rows still at the legacy default tuple to the new defaults; leave
    # any user-customised rows untouched.
    op.execute(
        """
        UPDATE station_episode_settings
        SET song_count = 9, commercial_count = 2, caller_count = 3
        WHERE song_count = 3 AND news_count = 1
          AND commercial_count = 1 AND caller_count = 1
        """
    )


def downgrade():
    op.alter_column("station_episode_settings", "song_count", server_default=sa.text("3"))
    op.alter_column("station_episode_settings", "commercial_count", server_default=sa.text("1"))
    op.alter_column("station_episode_settings", "caller_count", server_default=sa.text("1"))

    # Best-effort revert: rows still at the new default tuple go back to legacy.
    op.execute(
        """
        UPDATE station_episode_settings
        SET song_count = 3, commercial_count = 1, caller_count = 1
        WHERE song_count = 9 AND news_count = 1
          AND commercial_count = 2 AND caller_count = 3
        """
    )
