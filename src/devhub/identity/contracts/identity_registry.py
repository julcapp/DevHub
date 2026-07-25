"""Identity registry contract."""

from typing import Protocol

from devhub.identity.contracts.identity_provider import IdentityProvider
from devhub.identity.contracts.identity_strategy import IdentityStrategy


class IdentityRegistry(Protocol):
    """Resolve registered strategies and providers by stable name."""

    def get_strategy(self, name: str) -> IdentityStrategy:
        """Return a registered identity strategy."""
        ...

    def get_provider(self, name: str) -> IdentityProvider:
        """Return a registered identity provider."""
        ...
