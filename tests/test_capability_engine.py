from devhub.capabilities import (
    Capability,
    CapabilityAlreadyRegisteredError,
    CapabilityExecutor,
    CapabilityHandlerNotFoundError,
    CapabilityNotSupportedError,
    CapabilityRegistry,
)
from devhub.resources import Resource, ResourceURI


def make_resource(*capabilities: str) -> Resource:
    return Resource(
        uri=ResourceURI.parse("resource://local/projects/demo"),
        provider_id="local",
        title="Demo",
        capabilities=frozenset(capabilities),
    )


def test_capability_requires_namespace() -> None:
    try:
        Capability("read", "Read")
    except ValueError:
        pass
    else:
        raise AssertionError("Capability without namespace must be rejected")


def test_registry_rejects_duplicate_capability() -> None:
    registry = CapabilityRegistry()
    capability = Capability("capability.read", "Read")
    registry.register(capability)

    try:
        registry.register(capability)
    except CapabilityAlreadyRegisteredError:
        pass
    else:
        raise AssertionError("Duplicate capability must be rejected")


def test_executor_runs_provider_handler() -> None:
    registry = CapabilityRegistry()
    registry.register(Capability("capability.read", "Read"))
    executor = CapabilityExecutor(registry)
    executor.register_handler(
        "local",
        "capability.read",
        lambda resource, params: {"resource": resource.title, "path": params["path"]},
    )

    result = executor.execute(
        make_resource("capability.read"),
        "capability.read",
        {"path": "README.md"},
    )

    assert result == {"resource": "Demo", "path": "README.md"}


def test_executor_rejects_unsupported_capability() -> None:
    registry = CapabilityRegistry()
    registry.register(Capability("capability.write", "Write"))
    executor = CapabilityExecutor(registry)

    try:
        executor.execute(make_resource(), "capability.write")
    except CapabilityNotSupportedError:
        pass
    else:
        raise AssertionError("Unsupported resource capability must be rejected")


def test_executor_requires_registered_handler() -> None:
    registry = CapabilityRegistry()
    registry.register(Capability("capability.read", "Read"))
    executor = CapabilityExecutor(registry)

    try:
        executor.execute(make_resource("capability.read"), "capability.read")
    except CapabilityHandlerNotFoundError:
        pass
    else:
        raise AssertionError("Missing provider handler must be rejected")
