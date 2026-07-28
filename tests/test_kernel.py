from core.capabilities.capability_registry import CapabilityRegistry
from core.common.service import Service, ServiceStatus
from core.events.event_bus import Event, EventBus
from core.kernel.kernel import Kernel
from core.registry.service_registry import ServiceRegistry


class ExampleService(Service):
    service_id = "test.example"


def test_service_registry_resolves_service() -> None:
    registry = ServiceRegistry()
    service = ExampleService()
    registry.register(service)

    assert registry.resolve("test.example") is service
    assert len(registry) == 1


def test_capability_registry_resolves_provider() -> None:
    registry = CapabilityRegistry()
    provider = object()
    registry.register("test.capability", provider)

    assert registry.resolve("test.capability") is provider


def test_event_bus_delivers_event() -> None:
    bus = EventBus()
    received: list[Event] = []
    bus.subscribe("TestEvent", received.append)

    event = Event("TestEvent", {"value": 1})
    bus.publish(event)

    assert received == [event]


def test_kernel_starts_and_stops_registered_services() -> None:
    kernel = Kernel()
    service = ExampleService()
    kernel.services.register(service)

    metrics = kernel.start()

    assert kernel.is_ready is True
    assert service.status() is ServiceStatus.READY
    assert metrics.successful is True
    assert metrics.services == 1

    kernel.shutdown()

    assert kernel.is_ready is False
    assert service.status() is ServiceStatus.STOPPED
