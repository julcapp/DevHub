"""Create Engineering Objects core tables.

Revision ID: 0001_engineering_objects
Revises:
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_engineering_objects"
down_revision = None
branch_labels = None
depends_on = None

object_type = postgresql.ENUM(
    "PROJECT", "REPOSITORY", "STAR", "IDEA", "RESEARCH", "TECHNOLOGY",
    "ARTIFACT", "EVOLUTION", "ADR", "DOCUMENT",
    name="engineering_object_type", schema="core", create_type=False,
)
object_status = postgresql.ENUM(
    "DRAFT", "ACTIVE", "ARCHIVED",
    name="engineering_object_status", schema="core", create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    object_type.create(op.get_bind(), checkfirst=True)
    object_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "engineering_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("eo_id", sa.String(32), nullable=False),
        sa.Column("object_type", object_type, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", object_status, nullable=False, server_default="DRAFT"),
        sa.Column("source_system", sa.String(64)),
        sa.Column("source_key", sa.String(255)),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("eo_id", name="uq_engineering_objects_eo_id"),
        schema="core",
    )
    op.create_index("ix_engineering_objects_type_status", "engineering_objects", ["object_type", "status"], schema="core")

    op.create_table(
        "object_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.engineering_objects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.engineering_objects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("relation_type", sa.String(64), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source_id <> target_id", name="ck_object_relations_no_self_link"),
        sa.UniqueConstraint("source_id", "target_id", "relation_type", name="uq_object_relations_edge"),
        schema="core",
    )
    op.create_index("ix_object_relations_target", "object_relations", ["target_id", "relation_type"], schema="core")

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.engineering_objects.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False, server_default="system"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="core",
    )
    op.create_index("ix_audit_events_object_time", "audit_events", ["object_id", "created_at"], schema="core")


def downgrade() -> None:
    op.drop_table("audit_events", schema="core")
    op.drop_table("object_relations", schema="core")
    op.drop_table("engineering_objects", schema="core")
    object_status.drop(op.get_bind(), checkfirst=True)
    object_type.drop(op.get_bind(), checkfirst=True)
    op.execute("DROP SCHEMA IF EXISTS core")
