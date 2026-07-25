from __future__ import annotations

from .model import Resource, ResourceState
from .provider import ResourceProvider
from .registry import ResourceRegistry
from .uri import ResourceURI


class ProviderNotFoundError(KeyError):
    pass


class ResourceManager:
    """Application service coordinating providers and the resource registry."""

    def __init__(self, registry: ResourceRegistry | None = None) -> None:
        self.registry = registry or ResourceRegistry()
        self._providers: dict[str, ResourceProvider] = {}

    def register_provider(self, provider: ResourceProvider) -> None:
        if provider.provider_id in self._providers:
            raise ValueError(f"Provider already registered: {provider.provider_id}")
        self._providers[provider.provider_id] = provider

    def discover(self, provider_id: str) -> list[Resource]:
        provider = self._get_provider(provider_id)
        discovered: list[Resource] = []
        for resource in provider.discover():
            if not self.registry.contains(resource.uri):
                self.registry.register(resource)
            discovered.append(resource)
        return discovered

    def connect(self, provider_id: str, uri: ResourceURI | str) -> Resource:
        provider = self._get_provider(provider_id)
        parsed_uri = ResourceURI.parse(uri) if isinstance(uri, str) else uri
        resource = provider.connect(parsed_uri)
        resource.set_state(ResourceState.AVAILABLE)
        if not self.registry.contains(parsed_uri):
            self.registry.register(resource)
        return resource

    def disconnect(self, uri: ResourceURI | str) -> None:
        resource = self.registry.get(uri)
        provider = self._get_provider(resource.provider_id)
        provider.disconnect(resource)
        resource.set_state(ResourceState.OFFLINE)

    def _get_provider(self, provider_id: str) -> ResourceProvider:
        try:
            return self._providers[provider_id]
        except KeyError as error:
            raise ProviderNotFoundError(provider_id) from error
