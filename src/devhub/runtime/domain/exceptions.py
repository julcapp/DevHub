"""Runtime exception hierarchy."""


class DevHubRuntimeError(Exception):
    """Base class for all DevHub Runtime errors."""


class DiscoveryError(DevHubRuntimeError):
    """Raised when module discovery fails."""


class ManifestError(DevHubRuntimeError):
    """Raised when a module manifest is invalid."""


class DependencyError(DevHubRuntimeError):
    """Raised when dependencies cannot be resolved."""


class CircularDependencyError(DependencyError):
    """Raised when the dependency graph contains a cycle."""


class ModuleLoadError(DevHubRuntimeError):
    """Raised when a module cannot be instantiated."""


class LifecycleError(DevHubRuntimeError):
    """Raised when a lifecycle transition fails."""


class ModuleAlreadyLoadedError(DevHubRuntimeError):
    """Raised when a module is loaded more than once."""


class ModuleNotLoadedError(DevHubRuntimeError):
    """Raised when an operation targets an unloaded module."""


class HealthCheckError(DevHubRuntimeError):
    """Raised when module health evaluation fails."""


class CapabilityError(DevHubRuntimeError):
    """Raised when module capability metadata is invalid."""


class MetadataError(DevHubRuntimeError):
    """Raised when module metadata is invalid."""
