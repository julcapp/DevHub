from __future__ import annotations

from collections.abc import Iterator

from .model import Resource
from .uri import ResourceURI


class ResourceAlreadyRegisteredError(ValueError):
    pass


class ResourceNotFoundError(KeyError):
    pass


class ResourceRegistry:
    """In-memory source of truth for registered resources."""

    def __init__(self) -> None:
        self._by_uri: dict[ResourceURI, Resource] = {}

    def register(self, resource: Resource) -> Resource:
        if resource.uri in self._by_uri:
            raise ResourceAlreadyRegisteredError(str(resource.uri))
        self._by_uri[resource.uri] = resource
        return resource

    def get(self, uri: ResourceURI | str) -> Resource:
        key = ResourceURI.parse(uri) if isinstance(uri, str) else uri
        try:
            return self._by_uri[key]
        except KeyError as error:
            raise ResourceNotFoundError(str(key)) from error

    def remove(self, uri: ResourceURI | str) -> Resource:
        key = ResourceURI.parse(uri) if isinstance(uri, str) else uri
        try:
            return self._by_uri.pop(key)
        except KeyError as error:
            raise ResourceNotFoundError(str(key)) from error

    def contains(self, uri: ResourceURI | str) -> bool:
        key = ResourceURI.parse(uri) if isinstance(uri, str) else uri
        return key in self._by_uri

    def __iter__(self) -> Iterator[Resource]:
        return iter(self._by_uri.values())

    def __len__(self) -> int:
        return len(self._by_uri)
