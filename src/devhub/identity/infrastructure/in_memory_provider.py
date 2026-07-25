"""Thread-safe in-memory identity persistence provider."""

from threading import RLock

from devhub.identity.domain.exceptions import IdentityCollisionError
from devhub.identity.domain.validator import validate_identity_value


class InMemoryProvider:
    """Store registered identity values in process memory."""

    def __init__(self) -> None:
        self._identities: set[str] = set()
        self._lock = RLock()

    def contains(self, identity: str) -> bool:
        """Return whether an identity is already registered."""

        normalized_identity = validate_identity_value(identity)
        with self._lock:
            return normalized_identity in self._identities

    def save(self, identity: str) -> None:
        """Persist an identity or raise on collision."""

        normalized_identity = validate_identity_value(identity)
        with self._lock:
            if normalized_identity in self._identities:
                raise IdentityCollisionError(
                    f"Identity '{normalized_identity}' is already registered."
                )
            self._identities.add(normalized_identity)

    def count(self) -> int:
        """Return the number of stored identities."""

        with self._lock:
            return len(self._identities)

    def clear(self) -> None:
        """Remove all stored identities."""

        with self._lock:
            self._identities.clear()
