from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


EventHandler = Callable[[dict[str, Any]], None]


class ServiceRegistry:
    """Реестр общих сервисов платформы."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        if not name.strip():
            raise ValueError("Имя сервиса не может быть пустым")
        if name in self._services:
            raise KeyError(f"Сервис уже зарегистрирован: {name}")
        self._services[name] = service

    def resolve(self, name: str) -> Any:
        try:
            return self._services[name]
        except KeyError as exc:
            raise KeyError(f"Сервис не зарегистрирован: {name}") from exc

    def contains(self, name: str) -> bool:
        return name in self._services


class EventBus:
    """Синхронная событийная шина первого этапа."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    def publish(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        message = {
            "event": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(payload or {}),
        }
        for handler in tuple(self._handlers.get(event_name, [])):
            handler(message)


@dataclass(slots=True)
class PlatformKernel:
    """Минимальное ядро DevHub: сервисы, события и состояние запуска."""

    services: ServiceRegistry = field(default_factory=ServiceRegistry)
    events: EventBus = field(default_factory=EventBus)
    started: bool = False

    def start(self) -> None:
        if self.started:
            return
        self.started = True
        self.events.publish("platform.started", {"state": "READY"})

    def stop(self) -> None:
        if not self.started:
            return
        self.events.publish("platform.stopping", {"state": "STOPPING"})
        self.started = False
