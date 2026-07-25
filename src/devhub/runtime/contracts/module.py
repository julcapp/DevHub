"""Public module contract used by DevHub Runtime."""

from typing import Protocol, runtime_checkable

from devhub.runtime.domain.models import (
    Capability,
    HealthReport,
    ModuleMetadata,
    ModuleMetrics,
)


@runtime_checkable
class Module(Protocol):
    """Contract implemented by every loadable DevHub module."""

    def metadata(self) -> ModuleMetadata:
        """Return stable descriptive module metadata."""

    def capabilities(self) -> tuple[Capability, ...]:
        """Return capabilities exposed by the module."""

    def health(self) -> HealthReport:
        """Return the current health report."""

    def metrics(self) -> ModuleMetrics:
        """Return current operational metrics."""

    def configure(self) -> None:
        """Apply configuration before startup."""

    def start(self) -> None:
        """Start module services."""

    def stop(self) -> None:
        """Stop module services."""

    def dispose(self) -> None:
        """Release resources permanently."""
