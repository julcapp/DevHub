"""Tests for initial Identity Core infrastructure adapters."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from devhub.identity.contracts import IdentityProvider, IdentityStrategy
from devhub.identity.domain import IdentityCollisionError, InvalidIdentityError
from devhub.identity.infrastructure import InMemoryProvider, SequentialStrategy


def test_sequential_strategy_conforms_to_contract() -> None:
    strategy: IdentityStrategy = SequentialStrategy()

    assert strategy.name == "sequential"
    assert strategy.generate("module") == "module-00000001"
    assert strategy.generate("module") == "module-00000002"
    assert strategy.generate("workspace") == "workspace-00000001"


def test_sequential_strategy_supports_custom_start_and_width() -> None:
    strategy = SequentialStrategy(start=42, width=4)

    assert strategy.generate("event") == "event-0042"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"start": -1}, "start must be a non-negative integer"),
        ({"start": True}, "start must be a non-negative integer"),
        ({"width": 0}, "width must be a positive integer"),
        ({"width": True}, "width must be a positive integer"),
    ],
)
def test_sequential_strategy_rejects_invalid_configuration(
    kwargs: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        SequentialStrategy(**kwargs)  # type: ignore[arg-type]


def test_sequential_strategy_is_thread_safe() -> None:
    strategy = SequentialStrategy()

    with ThreadPoolExecutor(max_workers=8) as executor:
        values = list(executor.map(lambda _: strategy.generate("resource"), range(100)))

    assert len(values) == 100
    assert len(set(values)) == 100
    assert min(values) == "resource-00000001"
    assert max(values) == "resource-00000100"


def test_in_memory_provider_conforms_to_contract() -> None:
    provider: IdentityProvider = InMemoryProvider()

    assert provider.contains("module-00000001") is False
    provider.save("module-00000001")
    assert provider.contains("module-00000001") is True


def test_in_memory_provider_rejects_collisions() -> None:
    provider = InMemoryProvider()
    provider.save("module-00000001")

    with pytest.raises(IdentityCollisionError):
        provider.save("module-00000001")


def test_in_memory_provider_count_and_clear() -> None:
    provider = InMemoryProvider()
    provider.save("module-00000001")
    provider.save("module-00000002")

    assert provider.count() == 2
    provider.clear()
    assert provider.count() == 0


def test_infrastructure_validates_identity_values() -> None:
    strategy = SequentialStrategy()
    provider = InMemoryProvider()

    with pytest.raises(InvalidIdentityError):
        strategy.generate("Invalid Type")
    with pytest.raises(InvalidIdentityError):
        provider.save("Invalid Identity")
