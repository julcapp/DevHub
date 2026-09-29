"""Identity generation strategy contract."""

from typing import Protocol


class IdentityStrategy(Protocol):
    """Generate a raw identifier for a requested entity type."""

    @property
    def name(self) -> str:
        """Return the stable strategy name."""
        ...

    def generate(self, entity_type: str) -> str:
        """Generate a raw identifier value."""
        ...
