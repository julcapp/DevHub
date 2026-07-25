"""Clock contract for deterministic time access."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Supply the current time without hidden global state."""

    def now(self) -> datetime:
        """Return the current timezone-aware datetime."""
        ...
