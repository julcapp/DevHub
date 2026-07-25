from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Capability:
    """Stable description of an operation supported by a resource."""

    capability_id: str
    title: str
    description: str = ""
    version: str = "1.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = self.capability_id.strip().lower()
        if not normalized or "." not in normalized:
            raise ValueError(
                "capability_id must be a namespaced identifier, for example capability.read"
            )
        object.__setattr__(self, "capability_id", normalized)
