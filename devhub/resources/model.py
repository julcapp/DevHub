from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

from .uri import ResourceURI


class ResourceState(StrEnum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    SYNCING = "syncing"
    READ_ONLY = "read_only"


@dataclass(slots=True)
class Resource:
    """Provider-neutral representation of an external or local resource."""

    uri: ResourceURI
    provider_id: str
    title: str
    resource_id: str = field(default_factory=lambda: f"RES-{uuid4().hex[:12].upper()}")
    state: ResourceState = ResourceState.UNKNOWN
    capabilities: frozenset[str] = field(default_factory=frozenset)
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_state(self, state: ResourceState) -> None:
        self.state = state

    def supports(self, capability_id: str) -> bool:
        return capability_id in self.capabilities
