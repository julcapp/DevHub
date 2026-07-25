from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Event:
    """Immutable platform event exchanged between DevHub modules."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str | None = None
    correlation_id: str | None = None
    event_id: str = field(default_factory=lambda: f"EVT-{uuid4().hex[:12].upper()}")
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        normalized = self.name.strip().lower()
        if not normalized or "." not in normalized:
            raise ValueError("Event name must be a dotted identifier, for example resource.updated")
        object.__setattr__(self, "name", normalized)
