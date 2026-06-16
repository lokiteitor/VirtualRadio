"""Per-station deterministic episode numbering.

Revision ID: 0003_episode_number
Revises: 0002_station_episode_settings
Create Date: 2026-06-16

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_episode_number"
down_revision = "0002_station_episode_settings"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add nullable first so existing rows can be backfilled.
    op.add_column("episodes", sa.Column("episode_number", sa.Integer(), nullable=True))

    # 2. Backfill a per-station sequence ordered by creation time.
    op.execute(
        """
        UPDATE episodes AS e
        SET episode_number = sub.rn
        FROM (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY station_id ORDER BY created_at, id
            ) AS rn
            FROM episodes
        ) AS sub
        WHERE e.id = sub.id
        """
    )

    # 3. Enforce NOT NULL + per-station uniqueness.
    op.alter_column("episodes", "episode_number", nullable=False)
    op.create_unique_constraint(
        "uq_episodes_station_number", "episodes", ["station_id", "episode_number"]
    )


def downgrade():
    op.drop_constraint("uq_episodes_station_number", "episodes", type_="unique")
    op.drop_column("episodes", "episode_number")
