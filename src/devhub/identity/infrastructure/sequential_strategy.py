"""Deterministic sequential identity generation strategy."""

from threading import Lock

from devhub.identity.domain.validator import validate_identity_value


class SequentialStrategy:
    """Generate monotonically increasing identifiers per entity type.

    The strategy is process-local and thread-safe. Persistence of counters is
    intentionally outside this implementation and will be supplied by future
    providers when durable sequences are required.
    """

    def __init__(self, *, start: int = 1, width: int = 8) -> None:
        if isinstance(start, bool) or not isinstance(start, int) or start < 0:
            raise ValueError("start must be a non-negative integer")
        if isinstance(width, bool) or not isinstance(width, int) or width < 1:
            raise ValueError("width must be a positive integer")

        self._start = start
        self._width = width
        self._counters: dict[str, int] = {}
        self._lock = Lock()

    @property
    def name(self) -> str:
        """Return the stable strategy name."""

        return "sequential"

    def generate(self, entity_type: str) -> str:
        """Generate the next identifier for an entity type."""

        normalized_type = validate_identity_value(entity_type)

        with self._lock:
            current = self._counters.get(normalized_type, self._start)
            self._counters[normalized_type] = current + 1

        return f"{normalized_type}-{current:0{self._width}d}"
