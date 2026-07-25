"""Lifecycle orchestration contract."""

from typing import Protocol

from devhub.runtime.contracts.module import Module


class Lifecycle(Protocol):
    """Coordinate lifecycle operations for an already loaded module."""

    def configure(self, module: Module) -> None:
        """Configure a module."""

    def start(self, module: Module) -> None:
        """Start a module."""

    def stop(self, module: Module) -> None:
        """Stop a module."""

    def dispose(self, module: Module) -> None:
        """Dispose a module."""
