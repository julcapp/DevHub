import pytest

from app.platform.kernel import EventBus, PlatformKernel, ServiceRegistry


def test_service_registry_registers_and_resolves_service() -> None:
    registry = ServiceRegistry()
    service = object()

    registry.register("example", service)

    assert registry.resolve("example") is service
    assert registry.contains("example") is True


def test_service_registry_rejects_duplicate_name() -> None:
    registry = ServiceRegistry()
    registry.register("example", object())

    with pytest.raises(KeyError):
        registry.register("example", object())


def test_event_bus_publishes_message() -> None:
    bus = EventBus()
    received: list[dict[str, object]] = []
    bus.subscribe("asset.created", received.append)

    bus.publish("asset.created", {"asset_id": "A-001"})

    assert received[0]["event"] == "asset.created"
    assert received[0]["asset_id"] == "A-001"
    assert "timestamp" in received[0]


def test_kernel_start_and_stop_are_idempotent() -> None:
    kernel = PlatformKernel()
    events: list[str] = []
    kernel.events.subscribe("platform.started", lambda event: events.append(str(event["event"])))
    kernel.events.subscribe("platform.stopping", lambda event: events.append(str(event["event"])))

    kernel.start()
    kernel.start()
    kernel.stop()
    kernel.stop()

    assert events == ["platform.started", "platform.stopping"]
