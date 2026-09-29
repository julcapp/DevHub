"""Metrics collection contract."""

from typing import Protocol


class MetricsCollector(Protocol):
    """Collect module metrics without binding to a vendor."""

    def increment(self, metric: str, value: int = 1) -> None:
        """Increment a named counter."""
        ...
