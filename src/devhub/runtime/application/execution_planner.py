"""Build deterministic execution levels from a dependency graph."""

from devhub.runtime.application.dependency_resolver import DependencyResolver
from devhub.runtime.domain.dependency import DependencyGraph, ExecutionLevel, ExecutionPlan


class ExecutionPlanner:
    """Create dependency-safe execution levels for lifecycle orchestration."""

    def __init__(self, *, resolver: DependencyResolver | None = None) -> None:
        self._resolver = resolver or DependencyResolver()

    def plan(self, graph: DependencyGraph) -> ExecutionPlan:
        """Return a deterministic plan with independent modules grouped together."""

        order = self._resolver.resolve(graph)
        depth: dict[str, int] = {}
        for module_id in order:
            dependencies = graph.dependencies(module_id)
            depth[module_id] = (
                0 if not dependencies else 1 + max(depth[item] for item in dependencies)
            )

        if not depth:
            return ExecutionPlan(levels=())

        levels = tuple(
            ExecutionLevel(
                index=index,
                modules=tuple(sorted(module_id for module_id, value in depth.items() if value == index)),
            )
            for index in range(max(depth.values()) + 1)
        )
        return ExecutionPlan(levels=levels)
