"""Architecture and contract tests for DevHub Runtime."""

from datetime import UTC, datetime
from enum import Enum

from devhub.runtime import (
    Capability,
    HealthCheck,
    HealthReport,
    HealthStatus,
    ModuleMetadata,
    ModuleMetrics,
    ModuleState,
    RuntimeState,
)
from devhub.runtime.domain import (
    CircularDependencyError,
    DependencyError,
    DevHubRuntimeError,
    HealthCheckError,
    LifecycleError,
    ManifestError,
)


def test_runtime_states_are_enums() -> None:
    assert issubclass(ModuleState, Enum)
    assert issubclass(RuntimeState, Enum)
    assert issubclass(HealthStatus, Enum)


def test_exception_hierarchy_is_consistent() -> None:
    assert issubclass(ManifestError, DevHubRuntimeError)
    assert issubclass(DependencyError, DevHubRuntimeError)
    assert issubclass(CircularDependencyError, DependencyError)
    assert issubclass(LifecycleError, DevHubRuntimeError)
    assert issubclass(HealthCheckError, DevHubRuntimeError)


def test_introspection_models_are_immutable_value_objects() -> None:
    now = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    metadata = ModuleMetadata(
        id="devhub.runtime",
        name="DevHub Runtime",
        version="0.1.0",
        api_version=1,
    )
    capability = Capability(id="discover", name="Discover modules")
    check = HealthCheck(name="contracts", status=HealthStatus.HEALTHY)
    health = HealthReport(
        status=HealthStatus.HEALTHY,
        timestamp=now,
        checks=(check,),
    )
    metrics = ModuleMetrics(last_check=now)

    assert metadata.id == "devhub.runtime"
    assert capability.stable is True
    assert health.checks == (check,)
    assert metrics.last_check == now
