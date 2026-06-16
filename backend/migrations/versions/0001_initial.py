"""Initial schema: 12 tables, 4 enums, indexes and constraints.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-15

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

UUIDV7 = sa.text("uuidv7()")
NOW = sa.text("now()")

news_category = postgresql.ENUM(
    "Agricultura", "Transporte", "Economía", "Tecnología",
    "Clima", "Comunidad", "Política Local", "Sucesos Extraños",
    name="news_category", create_type=False,
)
news_tone = postgresql.ENUM(
    "Serio", "Sensacionalista", "Misterioso", "Absurdo",
    name="news_tone", create_type=False,
)
story_status = postgresql.ENUM(
    "active", "resolved", name="story_status", create_type=False,
)
job_status = postgresql.ENUM(
    "queued", "planning", "synthesizing", "mixing", "completed", "failed",
    name="job_status", create_type=False,
)


def _id_col():
    return sa.Column("id", postgresql.UUID(as_uuid=True), server_default=UUIDV7, nullable=False)


def _timestamps():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )


def _owner_col():
    return sa.Column(
        "owner_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )


def upgrade():
    bind = op.get_bind()
    for enum_type in (news_category, news_tone, story_status, job_status):
        enum_type.create(bind, checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        _id_col(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("role_code", sa.String(50), server_default=sa.text("'USER'"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("CREATE UNIQUE INDEX uq_users_email ON users (lower(email))")

    # --- roles ---
    op.create_table(
        "roles",
        _id_col(),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system_role", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("permissions", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    # --- stations ---
    op.create_table(
        "stations",
        _id_col(),
        _owner_col(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("host_name", sa.String(120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("personality", sa.Text(), nullable=True),
        sa.Column("frequency", sa.String(20), nullable=True),
        sa.Column("emoji", sa.String(16), nullable=True),
        sa.Column("color", sa.String(9), nullable=True),
        sa.Column("intro_templates", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("outro_templates", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_stations_owner_name"),
    )
    op.create_index("ix_stations_owner_id", "stations", ["owner_id"])

    # --- episodes ---
    op.create_table(
        "episodes",
        _id_col(),
        _owner_col(),
        sa.Column("station_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("duration", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("script_json", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("audio_path", sa.String(500), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_episodes_owner_id", "episodes", ["owner_id"])
    op.create_index("ix_episodes_station_id", "episodes", ["station_id"])

    # --- music_tracks ---
    op.create_table(
        "music_tracks",
        _id_col(),
        _owner_col(),
        sa.Column("file_path", sa.String(700), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("artist", sa.String(255), nullable=True),
        sa.Column("album", sa.String(255), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("file_hash", sa.CHAR(32), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "file_hash", name="uq_music_owner_hash"),
        sa.UniqueConstraint("owner_id", "file_path", name="uq_music_owner_path"),
    )
    op.create_index("ix_music_tracks_owner_id", "music_tracks", ["owner_id"])

    # --- news_items ---
    op.create_table(
        "news_items",
        _id_col(),
        _owner_col(),
        sa.Column("headline", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("full_script", sa.Text(), nullable=True),
        sa.Column("category", news_category, nullable=False),
        sa.Column("tone", news_tone, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_news_items_owner_id", "news_items", ["owner_id"])
    op.create_index("ix_news_active", "news_items", ["owner_id", "is_active"])

    # --- commercial_brands ---
    op.create_table(
        "commercial_brands",
        _id_col(),
        _owner_col(),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("slogan", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_brands_owner_name"),
    )
    op.create_index("ix_commercial_brands_owner_id", "commercial_brands", ["owner_id"])

    # --- commercials ---
    op.create_table(
        "commercials",
        _id_col(),
        _owner_col(),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("commercial_brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("script", sa.Text(), nullable=False),
        sa.Column("duration", sa.Float(), server_default=sa.text("30"), nullable=False),
        sa.Column("campaign", sa.String(150), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commercials_owner_id", "commercials", ["owner_id"])
    op.create_index("ix_commercials_brand_id", "commercials", ["brand_id"])

    # --- characters ---
    op.create_table(
        "characters",
        _id_col(),
        _owner_col(),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("role", sa.String(150), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("personality", sa.Text(), nullable=True),
        sa.Column("station_affinity", sa.Text(), nullable=True),
        sa.Column("first_appearance", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("last_appearance", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_characters_owner_name"),
    )
    op.create_index("ix_characters_owner_id", "characters", ["owner_id"])

    # --- character_memories ---
    op.create_table(
        "character_memories",
        _id_col(),
        _owner_col(),
        sa.Column("character_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("memory", sa.Text(), nullable=False),
        sa.Column("importance", sa.SmallInteger(), server_default=sa.text("5"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("importance BETWEEN 1 AND 10", name="ck_memories_importance"),
    )
    op.create_index("ix_character_memories_character_id", "character_memories", ["character_id"])
    op.create_index("ix_character_memories_owner_id", "character_memories", ["owner_id"])

    # --- story_events ---
    op.create_table(
        "story_events",
        _id_col(),
        _owner_col(),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("related_characters", sa.Text(), nullable=True),
        sa.Column("status", story_status, server_default=sa.text("'active'"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_story_events_owner_id", "story_events", ["owner_id"])
    op.create_index("ix_events_status", "story_events", ["owner_id", "status"])

    # --- generation_jobs ---
    op.create_table(
        "generation_jobs",
        _id_col(),
        _owner_col(),
        sa.Column("station_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", job_status, server_default=sa.text("'queued'"), nullable=False),
        sa.Column("progress", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generation_jobs_owner_id", "generation_jobs", ["owner_id"])
    op.create_index("ix_jobs_status", "generation_jobs", ["owner_id", "status"])


def downgrade():
    bind = op.get_bind()
    op.drop_table("generation_jobs")
    op.drop_table("story_events")
    op.drop_table("character_memories")
    op.drop_table("characters")
    op.drop_table("commercials")
    op.drop_table("commercial_brands")
    op.drop_table("news_items")
    op.drop_table("music_tracks")
    op.drop_table("episodes")
    op.drop_table("stations")
    op.drop_table("roles")
    op.execute("DROP INDEX IF EXISTS uq_users_email")
    op.drop_table("users")
    for enum_type in (job_status, story_status, news_tone, news_category):
        enum_type.drop(bind, checkfirst=True)
