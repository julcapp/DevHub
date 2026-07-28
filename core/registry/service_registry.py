"""Реестр сервисов Platform Core."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar, cast

from core.common.service import Service

TService = TypeVar("TService", bound=Service)


class ServiceRegistry:
    """Хранит единственные экземпляры сервисов и разрешает зависимости."""

    def __init__(self) -> None:
        self._services: dict[str, Service] = {}

    def register(self, service: Service, *, replace: bool = False) -> None:
        service_id = service.service_id
        if service_id in self._services and not replace:
            raise ValueError(f"Сервис уже зарегистрирован: {service_id}")
        self._services[service_id] = service

    def resolve(self, service_id: str, service_type: type[TService] | None = None) -> TService | Service:
        try:
            service = self._services[service_id]
        except KeyError as error:
            raise LookupError(f"Сервис не зарегистрирован: {service_id}") from error

        if service_type is not None and not isinstance(service, service_type):
            raise TypeError(
                f"Сервис {service_id} имеет тип {type(service).__name__}, "
                f"ожидался {service_type.__name__}"
            )
        return cast(TService, service) if service_type else service

    def contains(self, service_id: str) -> bool:
        return service_id in self._services

    def services(self) -> tuple[Service, ...]:
        return tuple(self._services.values())

    def service_ids(self) -> tuple[str, ...]:
        return tuple(self._services.keys())

    def validate_dependencies(self) -> None:
        missing: list[str] = []
        for service in self._services.values():
            for dependency in service.dependencies():
                if dependency not in self._services:
                    missing.append(f"{service.service_id} -> {dependency}")
        if missing:
            raise RuntimeError("Не найдены зависимости сервисов: " + ", ".join(missing))

    def __iter__(self) -> Iterable[Service]:
        return iter(self._services.values())

    def __len__(self) -> int:
        return len(self._services)
