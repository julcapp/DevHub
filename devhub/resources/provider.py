from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .model import Resource
from .uri import ResourceURI


class ResourceProvider(ABC):
    """Contract implemented by local and remote resource providers."""

    provider_id: str

    @abstractmethod
    def discover(self) -> Iterable[Resource]:
        """Return resources visible to this provider."""

    @abstractmethod
    def connect(self, uri: ResourceURI) -> Resource:
        """Connect to a resource and return its current representation."""

    @abstractmethod
    def disconnect(self, resource: Resource) -> None:
        """Release provider-owned handles associated with a resource."""
