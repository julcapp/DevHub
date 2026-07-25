from __future__ import annotations

from collections.abc import Iterator

from .model import Capability


class CapabilityAlreadyRegisteredError(ValueError):
    pass


class CapabilityNotFoundError(KeyError):
    pass


class CapabilityRegistry:
    """In-memory registry of public platform capabilities."""

    def __init__(self) -> None:
        self._items: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if capability.capability_id in self._items:
            raise CapabilityAlreadyRegisteredError(capability.capability_id)
        self._items[capability.capability_id] = capability

    def unregister(self, capability_id: str) -> Capability:
        try:
            return self._items.pop(capability_id.strip().lower())
        except KeyError as error:
            raise CapabilityNotFoundError(capability_id) from error

    def get(self, capability_id: str) -> Capability:
        try:
            return self._items[capability_id.strip().lower()]
        except KeyError as error:
            raise CapabilityNotFoundError(capability_id) from error

    def contains(self, capability_id: str) -> bool:
        return capability_id.strip().lower() in self._items

    def __iter__(self) -> Iterator[Capability]:
        return iter(self._items.values())

    def __len__(self) -> int:
        return len(self._items)
