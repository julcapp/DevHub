"""Application service orchestrating identity generation."""

from devhub.identity.contracts.clock import Clock
from devhub.identity.contracts.identity_registry import IdentityRegistry
from devhub.identity.domain.entity_id import EntityId
from devhub.identity.domain.entity_type import EntityType
from devhub.identity.domain.identity_descriptor import IdentityDescriptor


class IdentityService:
    """Generate, persist, and describe identities through registered adapters."""

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

    def generate(self, entity_type: EntityType) -> IdentityDescriptor:
        """Generate and persist one identity descriptor."""

        if not isinstance(entity_type, EntityType):
            raise TypeError("entity_type must be an EntityType")

        strategy = self._registry.get_strategy(self._strategy_name)
        provider = self._registry.get_provider(self._provider_name)
        raw_identity = strategy.generate(entity_type.value)
        identity = EntityId(raw_identity)
        provider.save(identity.value)

        return IdentityDescriptor(
            id=identity,
            entity_type=entity_type,
            strategy=strategy.name,
            created_at=self._clock.now(),
        )

    def validate(self, identity: str) -> bool:
        """Return whether an identity is present in the configured provider."""

        parsed = EntityId.parse(identity)
        provider = self._registry.get_provider(self._provider_name)
        return provider.contains(parsed.value)

    def parse(self, identity: str) -> EntityId:
        """Parse a serialized identity."""

        return EntityId.parse(identity)
