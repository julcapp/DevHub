from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

from .event import Event

EventHandler: TypeAlias = Callable[[Event], None]


@dataclass(frozen=True, slots=True)
class Subscription:
    event_name: str
    handler: EventHandler


class EventBus:
    """Small synchronous event bus with explicit subscriptions."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> Subscription:
        normalized = self._normalize_name(event_name)
        if handler not in self._handlers[normalized]:
            self._handlers[normalized].append(handler)
        return Subscription(normalized, handler)

    def unsubscribe(self, subscription: Subscription) -> bool:
        handlers = self._handlers.get(subscription.event_name)
        if not handlers or subscription.handler not in handlers:
            return False
        handlers.remove(subscription.handler)
        if not handlers:
            self._handlers.pop(subscription.event_name, None)
        return True

    def publish(self, event: Event) -> int:
        handlers = tuple(self._handlers.get(event.name, ()))
        wildcard_handlers = tuple(self._handlers.get("*", ()))
        delivered = 0
        for handler in (*handlers, *wildcard_handlers):
            handler(event)
            delivered += 1
        return delivered

    def clear(self) -> None:
        self._handlers.clear()

    def subscriber_count(self, event_name: str) -> int:
        return len(self._handlers.get(self._normalize_name(event_name), ()))

    @staticmethod
    def _normalize_name(event_name: str) -> str:
        normalized = event_name.strip().lower()
        if normalized != "*" and (not normalized or "." not in normalized):
            raise ValueError("Event name must be '*' or a dotted identifier")
        return normalized
