from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.indexer import ProjectIndexer
from app.knowledge import KnowledgeGraph


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


class ArchitectureWorkspaceController:
    """Готовит архитектурную сводку по локальному проекту без зависимости от Qt."""

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
        for edge in graph.edges:
            if edge.relation != "depends_on":
                continue
            source = graph.get_node(edge.source)
            target = graph.get_node(edge.target)
            if source is None or target is None:
                continue
            dependencies.append(f"{source.label} → {target.label}")

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
        )
