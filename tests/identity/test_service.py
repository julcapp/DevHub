"""Tests for Identity Core registry, clock, and service orchestration."""

from datetime import datetime, timezone

import pytest

from devhub.identity.application.registry import DefaultIdentityRegistry
from devhub.identity.application.service import IdentityService
from devhub.identity.domain import EntityType, UnknownProviderError, UnknownStrategyError
from devhub.identity.infrastructure import InMemoryProvider, SequentialStrategy, SystemClock


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)


def build_service() -> IdentityService:
    registry = DefaultIdentityRegistry()
    registry.register_strategy(SequentialStrategy())
    registry.register_provider("memory", InMemoryProvider())
    return IdentityService(registry=registry, clock=FixedClock())


def test_service_generates_persists_and_describes_identity() -> None:
    service = build_service()

    descriptor = service.generate(EntityType.MODULE)

    assert str(descriptor.id) == "module-00000001"
    assert descriptor.entity_type is EntityType.MODULE
    assert descriptor.strategy == "sequential"
    assert descriptor.created_at == datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    assert service.validate("module-00000001") is True


def test_service_parses_identity() -> None:
    service = build_service()
    assert str(service.parse("workspace-00000001")) == "workspace-00000001"


def test_registry_reports_missing_adapters() -> None:
    registry = DefaultIdentityRegistry()
    with pytest.raises(UnknownStrategyError):
        registry.get_strategy("missing")
    with pytest.raises(UnknownProviderError):
        registry.get_provider("missing")


def test_system_clock_is_timezone_aware_utc() -> None:
    current = SystemClock().now()
    assert current.tzinfo is not None
    assert current.utcoffset() == timezone.utc.utcoffset(current)
