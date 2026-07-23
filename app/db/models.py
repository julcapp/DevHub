from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EngineeringObjectType(str, enum.Enum):
    PROJECT = "PROJECT"
    REPOSITORY = "REPOSITORY"
    STAR = "STAR"
    IDEA = "IDEA"
    RESEARCH = "RESEARCH"
    TECHNOLOGY = "TECHNOLOGY"
    ARTIFACT = "ARTIFACT"
    EVOLUTION = "EVOLUTION"
    ADR = "ADR"
    DOCUMENT = "DOCUMENT"


class EngineeringObjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class EngineeringObject(Base):
    __tablename__ = "engineering_objects"
    __table_args__ = (
        UniqueConstraint("eo_id", name="uq_engineering_objects_eo_id"),
        Index("ix_engineering_objects_type_status", "object_type", "status"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eo_id: Mapped[str] = mapped_column(String(32), nullable=False)
    object_type: Mapped[EngineeringObjectType] = mapped_column(Enum(EngineeringObjectType, name="engineering_object_type", schema="core"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[EngineeringObjectStatus] = mapped_column(Enum(EngineeringObjectStatus, name="engineering_object_status", schema="core"), nullable=False, default=EngineeringObjectStatus.DRAFT)
    source_system: Mapped[str | None] = mapped_column(String(64))
    source_key: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    outgoing_relations: Mapped[list[ObjectRelation]] = relationship(back_populates="source", foreign_keys="ObjectRelation.source_id")
    incoming_relations: Mapped[list[ObjectRelation]] = relationship(back_populates="target", foreign_keys="ObjectRelation.target_id")


class ObjectRelation(Base):
    __tablename__ = "object_relations"
    __table_args__ = (
        UniqueConstraint("source_id", "target_id", "relation_type", name="uq_object_relations_edge"),
        CheckConstraint("source_id <> target_id", name="ck_object_relations_no_self_link"),
        Index("ix_object_relations_target", "target_id", "relation_type"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core.engineering_objects.id", ondelete="RESTRICT"), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core.engineering_objects.id", ondelete="RESTRICT"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    source: Mapped[EngineeringObject] = relationship(back_populates="outgoing_relations", foreign_keys=[source_id])
    target: Mapped[EngineeringObject] = relationship(back_populates="incoming_relations", foreign_keys=[target_id])


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_object_time", "object_id", "created_at"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core.engineering_objects.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
