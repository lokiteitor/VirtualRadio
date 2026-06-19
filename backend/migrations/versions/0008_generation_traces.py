"""Per-call AI usage traces + usage aggregates on generation jobs.

Adds ``generation_traces`` (one row per LLM/TTS call, for cost auditing) and six
usage-aggregate columns on ``generation_jobs`` (summed from the traces when a job
completes). Tokens and call counts only — no monetary cost is stored.

Revision ID: 0008_generation_traces
Revises: 0007_station_news_reads
Create Date: 2026-06-19

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0008_generation_traces"
down_revision = "0007_station_news_reads"
branch_labels = None
depends_on = None

UUIDV7 = sa.text("uuidv7()")
NOW = sa.text("now()")
ZERO = sa.text("0")

# Created explicitly in upgrade() (create_type=False mirrors 0001_initial / 0006).
trace_kind = postgresql.ENUM("llm", "tts", name="trace_kind", create_type=False)

_JOB_AGGREGATES = (
    "llm_calls",
    "llm_tokens_in",
    "llm_tokens_out",
    "tts_calls",
    "tts_cached",
    "tts_tokens",
)


def upgrade():
    bind = op.get_bind()
    trace_kind.create(bind, checkfirst=True)

    op.create_table(
        "generation_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=UUIDV7, nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "episode_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("episodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("kind", trace_kind, nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("tokens_in", sa.Integer(), server_default=ZERO, nullable=False),
        sa.Column("tokens_out", sa.Integer(), server_default=ZERO, nullable=False),
        sa.Column("total_tokens", sa.Integer(), server_default=ZERO, nullable=False),
        sa.Column("cached", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("latency_ms", sa.Integer(), server_default=ZERO, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generation_traces_owner_id", "generation_traces", ["owner_id"])
    op.create_index("ix_generation_traces_job_id", "generation_traces", ["job_id"])

    for column in _JOB_AGGREGATES:
        op.add_column(
            "generation_jobs",
            sa.Column(column, sa.Integer(), server_default=ZERO, nullable=False),
        )


def downgrade():
    for column in reversed(_JOB_AGGREGATES):
        op.drop_column("generation_jobs", column)
    op.drop_index("ix_generation_traces_job_id", table_name="generation_traces")
    op.drop_index("ix_generation_traces_owner_id", table_name="generation_traces")
    op.drop_table("generation_traces")
    op.execute("DROP TYPE IF EXISTS trace_kind")
