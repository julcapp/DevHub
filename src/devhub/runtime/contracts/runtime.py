"""Stable Runtime facade contract."""

from collections.abc import Sequence
from typing import Protocol

from devhub.runtime.contracts.module import Module
from devhub.runtime.domain.models import Capability, HealthReport, RuntimeState


class Runtime(Protocol):
    """Public control surface for the DevHub platform runtime."""

    @property
    def state(self) -> RuntimeState:
        """Return the current runtime state."""

    def discover(self) -> None:
        """Discover available module manifests."""

    def load(self) -> None:
        """Instantiate discovered modules."""

    def start(self) -> None:
        """Configure and start loaded modules."""

    def stop(self) -> None:
        """Stop and dispose loaded modules."""

    def modules(self) -> Sequence[Module]:
        """Return loaded modules in dependency order."""

    def health(self) -> dict[str, HealthReport]:
        """Return health reports indexed by module id."""

    def capabilities(self) -> dict[str, tuple[Capability, ...]]:
        """Return capabilities indexed by module id."""
