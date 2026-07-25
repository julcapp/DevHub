"""Immutable dependency graph and execution plan models."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    """Immutable directed graph where edges point to module dependencies."""

    _dependencies: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        normalized = {
            module_id: tuple(sorted(dependencies))
            for module_id, dependencies in sorted(self._dependencies.items())
        }
        object.__setattr__(self, "_dependencies", MappingProxyType(normalized))

    @property
    def nodes(self) -> tuple[str, ...]:
        """Return module ids in stable order."""

        return tuple(self._dependencies)

    def contains(self, module_id: str) -> bool:
        """Return whether a module exists in the graph."""

        return module_id in self._dependencies

    def dependencies(self, module_id: str) -> tuple[str, ...]:
        """Return direct dependencies for a module."""

        return self._dependencies[module_id]

    def dependents(self, module_id: str) -> tuple[str, ...]:
        """Return modules that directly depend on the supplied module."""

        return tuple(
            candidate
            for candidate in self.nodes
            if module_id in self._dependencies[candidate]
        )

    @property
    def roots(self) -> tuple[str, ...]:
        """Return modules without dependencies."""

        return tuple(module_id for module_id in self.nodes if not self.dependencies(module_id))

    @property
    def leaves(self) -> tuple[str, ...]:
        """Return modules without dependents."""

        return tuple(module_id for module_id in self.nodes if not self.dependents(module_id))


@dataclass(frozen=True, slots=True)
class ExecutionLevel:
    """Modules that can be executed concurrently."""

    index: int
    modules: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("Execution level index must be non-negative.")
        if not self.modules:
            raise ValueError("Execution level must contain at least one module.")
        if tuple(sorted(self.modules)) != self.modules:
            raise ValueError("Execution level modules must use stable ordering.")


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Deterministic dependency-safe module execution plan."""

    levels: tuple[ExecutionLevel, ...]
    warnings: tuple[str, ...] = ()

    @property
    def modules(self) -> tuple[str, ...]:
        """Return flattened module order."""

        return tuple(module_id for level in self.levels for module_id in level.modules)
