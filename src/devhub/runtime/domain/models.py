"""Immutable Runtime domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum, auto


class ModuleState(StrEnum):
    """Lifecycle state of one module instance."""

    DISCOVERED = auto()
    LOADED = auto()
    CONFIGURED = auto()
    STARTED = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    DISPOSED = auto()
    FAILED = auto()


class RuntimeState(StrEnum):
    """Lifecycle state of the Runtime itself."""

    CREATED = auto()
    DISCOVERING = auto()
    READY = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()


class LifecycleStage(StrEnum):
    """Operations managed by the lifecycle coordinator."""

    CONFIGURE = auto()
    START = auto()
    STOP = auto()
    DISPOSE = auto()


class HealthStatus(StrEnum):
    """Normalized health state exposed by every module."""

    UNKNOWN = auto()
    STARTING = auto()
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    STOPPED = auto()


@dataclass(frozen=True, slots=True)
class Capability:
    """One discoverable ability provided by a module."""

    id: str
    name: str
    stable: bool = True
    description: str = ""


@dataclass(frozen=True, slots=True)
class HealthCheck:
    """One atomic health check result."""

    name: str
    status: HealthStatus
    message: str = ""


@dataclass(frozen=True, slots=True)
class HealthReport:
    """Structured module health report."""

    status: HealthStatus
    timestamp: datetime
    checks: tuple[HealthCheck, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModuleMetadata:
    """Stable descriptive metadata for a Runtime module."""

    id: str
    name: str
    version: str
    api_version: int
    description: str = ""
    author: str = ""
    license: str = ""
    runtime_version: str = ""
    build_date: datetime | None = None
    homepage: str = ""
    repository: str = ""


@dataclass(frozen=True, slots=True)
class ModuleMetrics:
    """Minimal operational metrics exposed by a module."""

    uptime_seconds: float = 0.0
    start_time: datetime | None = None
    restart_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    last_check: datetime | None = None
    custom: dict[str, int | float | str] = field(default_factory=dict)
