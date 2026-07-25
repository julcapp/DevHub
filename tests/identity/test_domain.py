"""Unit tests for the Identity Core domain foundation."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from devhub.identity.domain import (
    EntityId,
    EntityType,
    IdentityDescriptor,
    InvalidIdentityError,
    ParseIdentityError,
)


def test_entity_type_values_are_stable() -> None:
    assert EntityType.MODULE.value == "module"
    assert EntityType.WORKSPACE.value == "workspace"
    assert EntityType.RESOURCE.value == "resource"
    assert EntityType.EVENT.value == "event"
    assert EntityType.DOCUMENT.value == "document"
    assert EntityType.SESSION.value == "session"


def test_entity_id_is_immutable_hashable_and_serializable() -> None:
    entity_id = EntityId("module.devhub-1")

    assert str(entity_id) == "module.devhub-1"
    assert entity_id.serialize() == "module.devhub-1"
    assert entity_id == EntityId("module.devhub-1")
    assert {entity_id: "value"}[EntityId("module.devhub-1")] == "value"

    with pytest.raises(FrozenInstanceError):
        entity_id.value = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "value",
    ["", "UPPERCASE", "-leading", "contains space", "x" * 129],
)
def test_entity_id_rejects_invalid_values(value: str) -> None:
    with pytest.raises(InvalidIdentityError):
        EntityId(value)


def test_entity_id_parse_normalizes_validation_error() -> None:
    with pytest.raises(ParseIdentityError):
        EntityId.parse("Invalid Value")


def test_identity_descriptor_is_immutable_and_serializable() -> None:
    created_at = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    descriptor = IdentityDescriptor(
        id=EntityId("module.devhub"),
        entity_type=EntityType.MODULE,
        strategy="sequential",
        created_at=created_at,
    )

    assert descriptor.to_dict() == {
        "id": "module.devhub",
        "entity_type": "module",
        "strategy": "sequential",
        "created_at": "2026-07-25T12:00:00+00:00",
        "version": 1,
    }

    with pytest.raises(FrozenInstanceError):
        descriptor.version = 2  # type: ignore[misc]


def test_identity_descriptor_requires_timezone_aware_datetime() -> None:
    with pytest.raises(InvalidIdentityError):
        IdentityDescriptor(
            id=EntityId("module.devhub"),
            entity_type=EntityType.MODULE,
            strategy="sequential",
            created_at=datetime(2026, 7, 25, 12, 0),
        )


@pytest.mark.parametrize("version", [0, -1, True])
def test_identity_descriptor_requires_positive_integer_version(version: int) -> None:
    with pytest.raises(InvalidIdentityError):
        IdentityDescriptor(
            id=EntityId("module.devhub"),
            entity_type=EntityType.MODULE,
            strategy="sequential",
            created_at=datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
            version=version,
        )
