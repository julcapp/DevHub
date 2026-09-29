"""Domain event publishing contract."""

from typing import Protocol


class EventPublisher(Protocol):
    """Publish identity events without coupling to an event bus."""

    def publish(self, event: object) -> None:
        """Publish one event."""
        ...
