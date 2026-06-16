"""Configurable Gemini TTS voices on stations, characters and commercials.

Adds a native ``gemini_voice`` ENUM (the 30 prebuilt Gemini voices) and nullable
voice columns: ``stations.host_voice`` / ``stations.reporter_voice``,
``characters.voice`` and ``commercials.voice``. Null means "use the role default"
(see ``app/integrations/tts_client.ROLE_VOICES``), so existing rows are unaffected.

Revision ID: 0006_tts_voices
Revises: 0005_episode_settings_defaults
Create Date: 2026-06-16

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0006_tts_voices"
down_revision = "0005_episode_settings_defaults"
branch_labels = None
depends_on = None

# Created explicitly in upgrade() (create_type=False mirrors 0001_initial / 0004).
_VOICE_NAMES = (
    "Achernar", "Achird", "Algenib", "Algieba", "Alnilam", "Aoede", "Autonoe",
    "Callirrhoe", "Charon", "Despina", "Enceladus", "Erinome", "Fenrir", "Gacrux",
    "Iapetus", "Kore", "Laomedeia", "Leda", "Orus", "Pulcherrima", "Puck",
    "Rasalgethi", "Sadachbia", "Sadaltager", "Schedar", "Sulafat", "Umbriel",
    "Vindemiatrix", "Zephyr", "Zubenelgenubi",
)
gemini_voice = postgresql.ENUM(*_VOICE_NAMES, name="gemini_voice", create_type=False)


def upgrade():
    bind = op.get_bind()
    gemini_voice.create(bind, checkfirst=True)
    op.add_column("stations", sa.Column("host_voice", gemini_voice, nullable=True))
    op.add_column("stations", sa.Column("reporter_voice", gemini_voice, nullable=True))
    op.add_column("characters", sa.Column("voice", gemini_voice, nullable=True))
    op.add_column("commercials", sa.Column("voice", gemini_voice, nullable=True))


def downgrade():
    op.drop_column("commercials", "voice")
    op.drop_column("characters", "voice")
    op.drop_column("stations", "reporter_voice")
    op.drop_column("stations", "host_voice")
    op.execute("DROP TYPE IF EXISTS gemini_voice")
