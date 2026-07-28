"""Минимальное ядро DevHub Platform Core."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from core.capabilities.capability_registry import CapabilityRegistry
from core.common.service import ServiceStatus
from core.events.event_bus import Event, EventBus
from core.registry.service_registry import ServiceRegistry


@dataclass(frozen=True, slots=True)
class KernelMetrics:
    startup_seconds: float
    services: int
    capabilities: int
    successful: bool


class Kernel:
    """Координирует регистрацию, запуск и остановку сервисов."""

    version = "0.1.0"

    def __init__(self) -> None:
        self.services = ServiceRegistry()
        self.capabilities = CapabilityRegistry()
        self.events = EventBus()
        self.metrics: KernelMetrics | None = None
        self._ready = False

    @property
    def is_ready(self) -> bool:
        return self._ready

    def start(self) -> KernelMetrics:
        started_at = perf_counter()
        successful = False
        try:
            self.services.validate_dependencies()
            for service in self.services:
                service.initialize()
            for service in self.services:
                service.start()
                if service.status() is not ServiceStatus.READY:
                    raise RuntimeError(f"Сервис не перешёл в Ready: {service.service_id}")
            self._ready = True
            self.events.publish(Event("KernelReady", {"version": self.version}))
            successful = True
        except Exception as error:
            self._ready = False
            self.events.publish(Event("KernelStartupFailed", {"error": str(error)}))
            raise
        finally:
            self.metrics = KernelMetrics(
                startup_seconds=perf_counter() - started_at,
                services=len(self.services),
                capabilities=len(self.capabilities),
                successful=successful,
            )
        return self.metrics

    def shutdown(self) -> None:
        for service in reversed(self.services.services()):
            service.shutdown()
        self._ready = False
        self.events.publish(Event("KernelStopped", {"version": self.version}))
