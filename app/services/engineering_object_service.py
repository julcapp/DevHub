from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.eo_id import format_eo_id
from app.db.models import (
    AuditEvent,
    EngineeringObject,
    EngineeringObjectStatus,
    EngineeringObjectType,
    ObjectRelation,
)


class EngineeringObjectService:
    """Application service for Engineering Objects and graph relations."""

    def __init__(self, session: Session):
        self.session = session

    def list_objects(self, limit: int = 200) -> list[EngineeringObject]:
        statement = (
            select(EngineeringObject)
            .order_by(EngineeringObject.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def create_object(
        self,
        object_type: EngineeringObjectType,
        title: str,
        description: str | None = None,
        actor: str = "local-user",
    ) -> EngineeringObject:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("Название инженерного объекта не может быть пустым")

        count_statement = select(func.count()).select_from(EngineeringObject).where(
            EngineeringObject.object_type == object_type
        )
        sequence_value = int(self.session.scalar(count_statement) or 0) + 1

        item = EngineeringObject(
            eo_id=format_eo_id(object_type.value, sequence_value),
            object_type=object_type,
            title=normalized_title,
            description=(description or "").strip() or None,
            status=EngineeringObjectStatus.DRAFT,
            source_system="devhub",
        )
        self.session.add(item)
        self.session.flush()
        self.session.add(
            AuditEvent(
                object_id=item.id,
                event_type="OBJECT_CREATED",
                actor=actor,
                payload={"eo_id": item.eo_id, "object_type": object_type.value},
            )
        )
        return item

    def archive_object(self, item: EngineeringObject, actor: str = "local-user") -> None:
        item.status = EngineeringObjectStatus.ARCHIVED
        item.archived_at = datetime.now(timezone.utc)
        self.session.add(
            AuditEvent(
                object_id=item.id,
                event_type="OBJECT_ARCHIVED",
                actor=actor,
                payload={"eo_id": item.eo_id},
            )
        )

    def relate(
        self,
        source: EngineeringObject,
        target: EngineeringObject,
        relation_type: str,
        actor: str = "local-user",
    ) -> ObjectRelation:
        normalized_type = relation_type.strip().upper()
        if not normalized_type:
            raise ValueError("Тип связи не может быть пустым")
        if source.id == target.id:
            raise ValueError("Объект нельзя связать с самим собой")

        relation = ObjectRelation(
            source_id=source.id,
            target_id=target.id,
            relation_type=normalized_type,
        )
        self.session.add(relation)
        self.session.flush()
        self.session.add(
            AuditEvent(
                object_id=source.id,
                event_type="RELATION_CREATED",
                actor=actor,
                payload={
                    "target_eo_id": target.eo_id,
                    "relation_type": normalized_type,
                },
            )
        )
        return relation
