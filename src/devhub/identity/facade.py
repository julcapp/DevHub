"""Stable public facade for Identity Core."""

from devhub.identity.bootstrap import get_service
from devhub.identity.domain.entity_id import EntityId
from devhub.identity.domain.entity_type import EntityType
from devhub.identity.domain.identity_descriptor import IdentityDescriptor


def generate(entity_type: EntityType) -> IdentityDescriptor:
    """Generate and persist an identity for the requested entity type."""

    return get_service().generate(entity_type)


def parse(identity: str) -> EntityId:
    """Parse a serialized identity into an immutable value object."""

    return get_service().parse(identity)


def validate(identity: str) -> bool:
    """Return whether an identity exists in the configured provider."""

    return get_service().validate(identity)


def describe(identity: str) -> dict[str, str | int]:
    """Return the stable serialized descriptor for an identity."""

    return get_service().describe(identity).to_dict()
