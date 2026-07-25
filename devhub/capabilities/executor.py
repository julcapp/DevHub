from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from devhub.resources.model import Resource

from .registry import CapabilityNotFoundError, CapabilityRegistry

CapabilityHandler = Callable[[Resource, dict[str, Any]], Any]


class CapabilityNotSupportedError(RuntimeError):
    pass


class CapabilityHandlerNotFoundError(LookupError):
    pass


@dataclass(slots=True)
class CapabilityExecution:
    capability_id: str
    resource_id: str
    parameters: dict[str, Any] = field(default_factory=dict)


class CapabilityExecutor:
    """Validates and executes resource capabilities through registered handlers."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry
        self._handlers: dict[tuple[str, str], CapabilityHandler] = {}

    def register_handler(
        self,
        provider_id: str,
        capability_id: str,
        handler: CapabilityHandler,
    ) -> None:
        capability_id = capability_id.strip().lower()
        self._registry.get(capability_id)
        self._handlers[(provider_id.strip().lower(), capability_id)] = handler

    def execute(
        self,
        resource: Resource,
        capability_id: str,
        parameters: dict[str, Any] | None = None,
    ) -> Any:
        capability_id = capability_id.strip().lower()
        try:
            self._registry.get(capability_id)
        except CapabilityNotFoundError:
            raise

        if not resource.supports(capability_id):
            raise CapabilityNotSupportedError(
                f"Resource {resource.resource_id} does not support {capability_id}"
            )

        key = (resource.provider_id.strip().lower(), capability_id)
        handler = self._handlers.get(key)
        if handler is None:
            raise CapabilityHandlerNotFoundError(
                f"No handler registered for provider={key[0]} capability={key[1]}"
            )

        return handler(resource, dict(parameters or {}))
