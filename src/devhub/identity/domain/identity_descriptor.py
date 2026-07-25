"""Immutable descriptor for a generated identity."""

from dataclasses import dataclass
from datetime import datetime

from devhub.identity.domain.entity_id import EntityId
from devhub.identity.domain.entity_type import EntityType
from devhub.identity.domain.exceptions import InvalidIdentityError
from devhub.identity.domain.validator import validate_strategy_name, validate_version


@dataclass(frozen=True, slots=True)
class IdentityDescriptor:
    """Domain passport describing an identity and its provenance."""

    id: EntityId
    entity_type: EntityType
    strategy: str
    created_at: datetime
    version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.id, EntityId):
            raise InvalidIdentityError("Descriptor id must be an EntityId.")
        if not isinstance(self.entity_type, EntityType):
            raise InvalidIdentityError("Descriptor entity_type must be an EntityType.")
        if not isinstance(self.created_at, datetime):
            raise InvalidIdentityError("Descriptor created_at must be a datetime.")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise InvalidIdentityError("Descriptor created_at must be timezone-aware.")
        validate_strategy_name(self.strategy)
        validate_version(self.version)

    def to_dict(self) -> dict[str, str | int]:
        """Serialize the descriptor to stable primitive values."""

        return {
            "id": self.id.serialize(),
            "entity_type": self.entity_type.value,
            "strategy": self.strategy,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }
