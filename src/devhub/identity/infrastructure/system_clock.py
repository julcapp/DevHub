"""Timezone-aware system clock adapter."""

from datetime import datetime, timezone


class SystemClock:
    """Return current UTC time through the Clock contract."""

    def now(self) -> datetime:
        """Return the current timezone-aware UTC datetime."""

        return datetime.now(timezone.utc)
