"""Базовый контракт сервисов Platform Core."""

from __future__ import annotations

from abc import ABC
from enum import StrEnum
from typing import Any


class ServiceStatus(StrEnum):
    """Стандартные состояния жизненного цикла сервиса."""

    CREATED = "created"
    INITIALIZED = "initialized"
    STARTING = "starting"
    READY = "ready"
    BUSY = "busy"
    DEGRADED = "degraded"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DISABLED = "disabled"


class ServiceHealth(StrEnum):
    """Сводная оценка работоспособности сервиса."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Service(ABC):
    """Минимальный контракт управляемого сервиса DevHub."""

    service_id = "core.service"
    service_version = "0.1.0"

    def __init__(self) -> None:
        self._status = ServiceStatus.CREATED
        self._last_error: str | None = None

    def initialize(self) -> None:
        self._status = ServiceStatus.INITIALIZED

    def start(self) -> None:
        self._status = ServiceStatus.STARTING
        self._status = ServiceStatus.READY

    def stop(self) -> None:
        self._status = ServiceStatus.STOPPING
        self._status = ServiceStatus.STOPPED

    def shutdown(self) -> None:
        if self._status is not ServiceStatus.STOPPED:
            self.stop()

    def status(self) -> ServiceStatus:
        return self._status

    def health(self) -> ServiceHealth:
        if self._status in {ServiceStatus.READY, ServiceStatus.BUSY}:
            return ServiceHealth.HEALTHY
        if self._status is ServiceStatus.DEGRADED:
            return ServiceHealth.DEGRADED
        if self._status is ServiceStatus.ERROR:
            return ServiceHealth.UNHEALTHY
        return ServiceHealth.UNKNOWN

    def version(self) -> str:
        return self.service_version

    def dependencies(self) -> tuple[str, ...]:
        return ()

    def capabilities(self) -> tuple[str, ...]:
        return ()

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.service_id,
            "version": self.version(),
            "status": self.status().value,
            "health": self.health().value,
            "dependencies": list(self.dependencies()),
            "capabilities": list(self.capabilities()),
            "last_error": self._last_error,
        }

    def fail(self, error: Exception | str) -> None:
        self._last_error = str(error)
        self._status = ServiceStatus.ERROR
