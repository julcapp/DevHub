"""In-process registry for Identity Core strategies and providers."""

from threading import RLock

from devhub.identity.contracts.identity_provider import IdentityProvider
from devhub.identity.contracts.identity_strategy import IdentityStrategy
from devhub.identity.domain.exceptions import UnknownStrategyError
from devhub.identity.domain.validator import validate_strategy_name


class DefaultIdentityRegistry:
    """Register and resolve Identity Core adapters by stable name."""

    def __init__(self) -> None:
        self._strategies: dict[str, IdentityStrategy] = {}
        self._providers: dict[str, IdentityProvider] = {}
        self._lock = RLock()

    def register_strategy(self, strategy: IdentityStrategy) -> None:
        """Register a strategy under its stable name."""

        name = validate_strategy_name(strategy.name)
        with self._lock:
            if name in self._strategies:
                raise ValueError(f"Strategy '{name}' is already registered.")
            self._strategies[name] = strategy

    def register_provider(self, name: str, provider: IdentityProvider) -> None:
        """Register a provider under a stable name."""

        normalized_name = validate_strategy_name(name)
        with self._lock:
            if normalized_name in self._providers:
                raise ValueError(f"Provider '{normalized_name}' is already registered.")
            self._providers[normalized_name] = provider

    def get_strategy(self, name: str) -> IdentityStrategy:
        """Return a registered strategy."""

        normalized_name = validate_strategy_name(name)
        with self._lock:
            try:
                return self._strategies[normalized_name]
            except KeyError as error:
                raise UnknownStrategyError(
                    f"Identity strategy '{normalized_name}' is not registered."
                ) from error

    def get_provider(self, name: str) -> IdentityProvider:
        """Return a registered provider."""

        normalized_name = validate_strategy_name(name)
        with self._lock:
            try:
                return self._providers[normalized_name]
            except KeyError as error:
                raise LookupError(
                    f"Identity provider '{normalized_name}' is not registered."
                ) from error
