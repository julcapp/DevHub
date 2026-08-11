from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.indexer import ProjectIndexer
from app.knowledge import KnowledgeGraph


@dataclass(frozen=True)
class ModuleArchitecture:
    name: str
    path: str
    dependencies: tuple[str, ...]
    dependents: tuple[str, ...]
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureSummary:
    project_name: str
    project_path: str
    files: int
    folders: int
    modules: int
    classes: int
    methods: int
    functions: int
    imports: int
    internal_dependencies: int
    nodes_total: int
    edges_total: int
    dependencies: tuple[str, ...]
    module_details: tuple[ModuleArchitecture, ...] = ()
    cycles: tuple[tuple[str, ...], ...] = ()
    warnings: tuple[str, ...] = ()


class ArchitectureWorkspaceController:
    """Готовит архитектурную сводку, карточки модулей и предупреждения."""

    def __init__(self, indexer: ProjectIndexer | None = None) -> None:
        self.indexer = indexer or ProjectIndexer()
        self.graph: KnowledgeGraph | None = None

    def analyze(self, root: Path) -> ArchitectureSummary:
        graph, result = self.indexer.build_graph(root)
        self.graph = graph
        counts: dict[str, int] = {}
        for node in graph.nodes:
            counts[node.kind] = counts.get(node.kind, 0) + 1

        dependencies: list[str] = []
        adjacency: dict[str, set[str]] = {}
        module_details: list[ModuleArchitecture] = []
        modules = sorted((node for node in graph.nodes if node.kind == "Module"), key=lambda n: n.label)
        for module in modules:
            adjacency[module.label] = set()

        for edge in graph.edges:
            if edge.relation != "depends_on":
                continue
            source = graph.get_node(edge.source)
            target = graph.get_node(edge.target)
            if source and target:
                dependencies.append(f"{source.label} → {target.label}")
                adjacency.setdefault(source.label, set()).add(target.label)
                adjacency.setdefault(target.label, set())

        for module in modules:
            outgoing = []
            incoming = []
            symbols = []
            for edge in graph.edges:
                if edge.relation == "depends_on" and edge.source == module.id:
                    target = graph.get_node(edge.target)
                    if target:
                        outgoing.append(target.label)
                elif edge.relation == "depends_on" and edge.target == module.id:
                    source = graph.get_node(edge.source)
                    if source:
                        incoming.append(source.label)
                elif edge.relation == "defines" and edge.source == module.id:
                    symbol = graph.get_node(edge.target)
                    if symbol and symbol.kind in {"Class", "Method", "Function"}:
                        symbols.append(f"{symbol.kind}: {symbol.label}")
            module_details.append(ModuleArchitecture(
                name=module.label,
                path=str(module.attributes.get("path", "")),
                dependencies=tuple(sorted(set(outgoing))),
                dependents=tuple(sorted(set(incoming))),
                symbols=tuple(sorted(symbols)),
            ))

        cycles = self._find_cycles(adjacency)
        warnings = self._build_warnings(cycles, adjacency)

        return ArchitectureSummary(
            project_name=root.resolve().name,
            project_path=str(root.resolve()),
            files=result.files_indexed,
            folders=result.folders_indexed,
            modules=counts.get("Module", 0),
            classes=counts.get("Class", 0),
            methods=counts.get("Method", 0),
            functions=counts.get("Function", 0),
            imports=result.imports_indexed,
            internal_dependencies=result.internal_dependencies_resolved,
            nodes_total=result.nodes_total,
            edges_total=result.edges_total,
            dependencies=tuple(sorted(dependencies)),
            module_details=tuple(module_details),
            cycles=cycles,
            warnings=warnings,
        )

    @staticmethod
    def _find_cycles(adjacency: dict[str, set[str]]) -> tuple[tuple[str, ...], ...]:
        """Находит простые циклы и нормализует их, чтобы не возвращать дубликаты."""
        found: set[tuple[str, ...]] = set()

        def canonical(cycle: list[str]) -> tuple[str, ...]:
            body = cycle[:-1]
            rotations = [tuple(body[i:] + body[:i]) for i in range(len(body))]
            return min(rotations)

        def visit(start: str, current: str, path: list[str], seen: set[str]) -> None:
            for target in adjacency.get(current, set()):
                if target == start and len(path) > 1:
                    found.add(canonical(path + [start]))
                elif target not in seen and len(path) < len(adjacency):
                    visit(start, target, path + [target], seen | {target})

        for node in sorted(adjacency):
            visit(node, node, [node], {node})

        return tuple(sorted(found))

    @staticmethod
    def _build_warnings(
        cycles: tuple[tuple[str, ...], ...],
        adjacency: dict[str, set[str]],
    ) -> tuple[str, ...]:
        warnings: list[str] = []
        for cycle in cycles:
            chain = " → ".join((*cycle, cycle[0]))
            warnings.append(f"Циклическая зависимость: {chain}")
        for module, targets in sorted(adjacency.items()):
            if len(targets) >= 5:
                warnings.append(
                    f"Высокая связанность: {module} зависит от {len(targets)} внутренних модулей"
                )
        return tuple(warnings)
