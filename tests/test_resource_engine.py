from collections.abc import Iterable

import pytest

from devhub.resources import (
    ProviderNotFoundError,
    Resource,
    ResourceAlreadyRegisteredError,
    ResourceManager,
    ResourceProvider,
    ResourceRegistry,
    ResourceState,
    ResourceURI,
)


class FakeProvider(ResourceProvider):
    provider_id = "fake"

    def discover(self) -> Iterable[Resource]:
        yield Resource(
            uri=ResourceURI.parse("resource://fake/project"),
            provider_id=self.provider_id,
            title="Project",
            capabilities=frozenset({"capability.read"}),
        )

    def connect(self, uri: ResourceURI) -> Resource:
        return Resource(uri=uri, provider_id=self.provider_id, title="Connected")

    def disconnect(self, resource: Resource) -> None:
        return None


def test_resource_uri_round_trip() -> None:
    uri = ResourceURI.parse("resource://github/julcapp/DevHub")

    assert uri.scheme == "resource"
    assert uri.authority == "github"
    assert uri.path == "julcapp/DevHub"
    assert str(uri) == "resource://github/julcapp/DevHub"


def test_registry_rejects_duplicate_uri() -> None:
    registry = ResourceRegistry()
    resource = Resource(
        uri=ResourceURI.parse("resource://fake/project"),
        provider_id="fake",
        title="Project",
    )
    registry.register(resource)

    with pytest.raises(ResourceAlreadyRegisteredError):
        registry.register(resource)


def test_manager_discovers_and_connects_resources() -> None:
    manager = ResourceManager()
    manager.register_provider(FakeProvider())

    discovered = manager.discover("fake")
    connected = manager.connect("fake", "resource://fake/connected")

    assert len(discovered) == 1
    assert discovered[0].supports("capability.read")
    assert connected.state is ResourceState.AVAILABLE
    assert len(manager.registry) == 2


def test_manager_rejects_unknown_provider() -> None:
    manager = ResourceManager()

    with pytest.raises(ProviderNotFoundError):
        manager.discover("missing")
