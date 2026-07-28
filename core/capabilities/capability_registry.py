"""Реестр возможностей модульной платформы."""

from __future__ import annotations

from typing import Any, TypeVar, cast

TCapability = TypeVar("TCapability")


class CapabilityRegistry:
    """Связывает стабильный идентификатор возможности с её провайдером."""

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}

    def register(self, capability_id: str, provider: Any, *, replace: bool = False) -> None:
        capability_id = capability_id.strip()
        if not capability_id:
            raise ValueError("Идентификатор возможности не может быть пустым")
        if capability_id in self._providers and not replace:
            raise ValueError(f"Возможность уже зарегистрирована: {capability_id}")
        self._providers[capability_id] = provider

    def resolve(
        self,
        capability_id: str,
        provider_type: type[TCapability] | None = None,
    ) -> TCapability | Any:
        try:
            provider = self._providers[capability_id]
        except KeyError as error:
            raise LookupError(f"Возможность не зарегистрирована: {capability_id}") from error

        if provider_type is not None and not isinstance(provider, provider_type):
            raise TypeError(
                f"Провайдер {capability_id} имеет тип {type(provider).__name__}, "
                f"ожидался {provider_type.__name__}"
            )
        return cast(TCapability, provider) if provider_type else provider

    def unregister(self, capability_id: str) -> None:
        self._providers.pop(capability_id, None)

    def contains(self, capability_id: str) -> bool:
        return capability_id in self._providers

    def capability_ids(self) -> tuple[str, ...]:
        return tuple(self._providers.keys())

    def __len__(self) -> int:
        return len(self._providers)
