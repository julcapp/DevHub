"""Tests for the Identity Core public facade and bootstrap."""

from datetime import UTC, datetime

import pytest

import devhub.identity as identity
from devhub.identity.application.service import IdentityService
from devhub.identity.bootstrap import build_service, configure, get_service, reset
from devhub.identity.domain import EntityType, IdentityNotFoundError


class FixedClock:
    def __init__(self, value: datetime) -> None:
        self._value = value

    def now(self) -> datetime:
        return self._value


@pytest.fixture(autouse=True)
def reset_identity_runtime() -> None:
    reset()
    yield
    reset()


def test_public_api_is_frozen() -> None:
    assert sorted(identity.__all__) == ["describe", "generate", "parse", "validate"]


def test_bootstrap_is_lazy_singleton() -> None:
    assert get_service() is get_service()


def test_public_facade_full_scenario() -> None:
    descriptor = identity.generate(EntityType.MODULE)

    assert descriptor.id.value == "module-00000001"
    assert identity.parse(descriptor.id.value) == descriptor.id
    assert identity.validate(descriptor.id.value) is True
    assert identity.describe(descriptor.id.value) == descriptor.to_dict()


def test_describe_rejects_unknown_identity() -> None:
    with pytest.raises(IdentityNotFoundError):
        identity.describe("module-00000001")


def test_runtime_can_be_overridden() -> None:
    fixed_time = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    service = build_service(clock=FixedClock(fixed_time))
    assert isinstance(service, IdentityService)

    configure(service=service)
    descriptor = identity.generate(EntityType.WORKSPACE)

    assert descriptor.created_at == fixed_time
    assert identity.describe(descriptor.id.value)["entity_type"] == "workspace"


def test_configure_requires_identity_service() -> None:
    with pytest.raises(TypeError):
        configure(service=object())  # type: ignore[arg-type]
