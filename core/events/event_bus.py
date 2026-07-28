"""Минимальная синхронная шина событий Kernel v0.1."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

EventHandler = Callable[["Event"], None]


@dataclass(frozen=True, slots=True)
class Event:
    """Неизменяемое событие платформы."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "kernel"
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """Публикует события подписчикам без прямых связей между модулями."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        handlers = self._subscribers.get(event_name, [])
        if handler in handlers:
            handlers.remove(handler)
        if not handlers:
            self._subscribers.pop(event_name, None)

    def publish(self, event: Event) -> None:
        handlers = tuple(self._subscribers.get(event.name, ()))
        wildcard_handlers = tuple(self._subscribers.get("*", ()))
        for handler in handlers + wildcard_handlers:
            handler(event)

    def clear(self) -> None:
        self._subscribers.clear()

    def subscriber_count(self, event_name: str | None = None) -> int:
        if event_name is not None:
            return len(self._subscribers.get(event_name, ()))
        return sum(len(handlers) for handlers in self._subscribers.values())
