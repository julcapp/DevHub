"""Identity persistence provider contract."""

from typing import Protocol


class IdentityProvider(Protocol):
    """Persist and retrieve identity descriptors."""

    def contains(self, identity: str) -> bool:
        """Return whether an identity is already registered."""
        ...

    def save(self, identity: str) -> None:
        """Persist an identity."""
        ...
