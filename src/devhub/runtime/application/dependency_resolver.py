"""Dependency graph validation and deterministic resolution."""

from devhub.runtime.domain.dependency import DependencyGraph
from devhub.runtime.domain.exceptions import CircularDependencyError


class DependencyResolver:
    """Validate dependency graphs and produce a stable topological order."""

    def resolve(self, graph: DependencyGraph) -> tuple[str, ...]:
        """Return dependency-first order or raise with the complete cycle path."""

        state: dict[str, int] = {module_id: 0 for module_id in graph.nodes}
        order: list[str] = []
        stack: list[str] = []

        def visit(module_id: str) -> None:
            current = state[module_id]
            if current == 2:
                return
            if current == 1:
                cycle_start = stack.index(module_id)
                cycle = (*stack[cycle_start:], module_id)
                raise CircularDependencyError(
                    "Circular module dependency: " + " -> ".join(cycle) + "."
                )

            state[module_id] = 1
            stack.append(module_id)
            for dependency in graph.dependencies(module_id):
                visit(dependency)
            stack.pop()
            state[module_id] = 2
            order.append(module_id)

        for module_id in graph.nodes:
            visit(module_id)

        return tuple(order)
