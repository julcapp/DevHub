"""Application service orchestrating identity generation."""

from threading import RLock

from devhub.identity.contracts.clock import Clock
from devhub.identity.contracts.identity_registry import IdentityRegistry
from devhub.identity.domain.entity_id import EntityId
from devhub.identity.domain.entity_type import EntityType
from devhub.identity.domain.exceptions import IdentityNotFoundError, InvalidEntityTypeError
from devhub.identity.domain.identity_descriptor import IdentityDescriptor


class IdentityService:
    """Generate, persist, validate, parse, and describe identities."""

    def __init__(
        self,
        *,
        registry: IdentityRegistry,
        clock: Clock,
        strategy_name: str = "sequential",
        provider_name: str = "memory",
    ) -> None:
        self._registry = registry
        self._clock = clock
        self._strategy_name = strategy_name
        self._provider_name = provider_name
        self._descriptors: dict[str, IdentityDescriptor] = {}
        self._lock = RLock()

    def generate(self, entity_type: EntityType) -> IdentityDescriptor:
        """Generate and persist one identity descriptor."""

        if not isinstance(entity_type, EntityType):
            raise InvalidEntityTypeError("entity_type must be an EntityType")

        strategy = self._registry.get_strategy(self._strategy_name)
        provider = self._registry.get_provider(self._provider_name)
        raw_identity = strategy.generate(entity_type.value)
        identity = EntityId(raw_identity)
        provider.save(identity.value)

        descriptor = IdentityDescriptor(
            id=identity,
            entity_type=entity_type,
            strategy=strategy.name,
            created_at=self._clock.now(),
        )
        with self._lock:
            self._descriptors[identity.value] = descriptor
        return descriptor

    def validate(self, identity: str) -> bool:
        """Return whether an identity is present in the configured provider."""

        parsed = EntityId.parse(identity)
        provider = self._registry.get_provider(self._provider_name)
        return provider.contains(parsed.value)

    def parse(self, identity: str) -> EntityId:
        """Parse a serialized identity."""

        return EntityId.parse(identity)

    def describe(self, identity: str) -> IdentityDescriptor:
        """Return the descriptor recorded for a generated identity."""

        parsed = EntityId.parse(identity)
        with self._lock:
            try:
                return self._descriptors[parsed.value]
            except KeyError as error:
                raise IdentityNotFoundError(
                    f"Identity descriptor '{parsed.value}' is not available."
                ) from error
