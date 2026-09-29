"""Lazy composition root for Identity Core."""

from threading import RLock

from devhub.identity.application.registry import DefaultIdentityRegistry
from devhub.identity.application.service import IdentityService
from devhub.identity.contracts.clock import Clock
from devhub.identity.contracts.identity_provider import IdentityProvider
from devhub.identity.contracts.identity_strategy import IdentityStrategy
from devhub.identity.infrastructure.in_memory_provider import InMemoryProvider
from devhub.identity.infrastructure.sequential_strategy import SequentialStrategy
from devhub.identity.infrastructure.system_clock import SystemClock

_lock = RLock()
_service: IdentityService | None = None


def build_service(
    *,
    strategy: IdentityStrategy | None = None,
    provider: IdentityProvider | None = None,
    clock: Clock | None = None,
) -> IdentityService:
    """Build an isolated Identity Core service with explicit dependencies."""

    registry = DefaultIdentityRegistry()
    registry.register_strategy(strategy or SequentialStrategy())
    registry.register_provider("memory", provider or InMemoryProvider())
    return IdentityService(registry=registry, clock=clock or SystemClock())


def get_service() -> IdentityService:
    """Return the lazily initialized process-wide Identity Core service."""

    global _service
    with _lock:
        if _service is None:
            _service = build_service()
        return _service


def configure(*, service: IdentityService) -> None:
    """Replace the process-wide service, primarily for integration and tests."""

    if not isinstance(service, IdentityService):
        raise TypeError("service must be an IdentityService")

    global _service
    with _lock:
        _service = service


def reset() -> None:
    """Clear the process-wide service so the next call rebuilds defaults."""

    global _service
    with _lock:
        _service = None
