"""Per-station script language on episode settings.

Revision ID: 0004_settings_language
Revises: 0003_episode_number
Create Date: 2026-06-16

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004_settings_language"
down_revision = "0003_episode_number"
branch_labels = None
depends_on = None

# Created explicitly in upgrade() (create_type=False mirrors 0001_initial).
language = postgresql.ENUM("es", "en", name="language", create_type=False)


def upgrade():
    bind = op.get_bind()
    language.create(bind, checkfirst=True)
    op.add_column(
        "station_episode_settings",
        sa.Column(
            "language",
            language,
            server_default=sa.text("'es'"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("station_episode_settings", "language")
    op.execute("DROP TYPE IF EXISTS language")
