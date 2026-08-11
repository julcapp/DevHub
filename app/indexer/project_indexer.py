from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.indexer.file_scanner import FileScanner
from app.knowledge import Edge, KnowledgeGraph, Node


@dataclass(frozen=True)
class ProjectIndexResult:
    project_id: str
    files_indexed: int
    folders_indexed: int
    nodes_total: int
    edges_total: int


class ProjectIndexer:
    """Строит базовый граф Project -> Folder -> File для локального проекта."""

    def __init__(self, scanner: FileScanner | None = None) -> None:
        self.scanner = scanner or FileScanner()

    def build_graph(self, root: Path, graph: KnowledgeGraph | None = None) -> tuple[KnowledgeGraph, ProjectIndexResult]:
        root = root.resolve()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(root)

        graph = graph or KnowledgeGraph()
        project_id = f"project:{root.as_posix()}"
        graph.add_node(
            Node(
                id=project_id,
                kind="Project",
                label=root.name,
                attributes={"path": str(root)},
            )
        )

        folder_ids: set[str] = set()
        files = self.scanner.scan(root)

        for item in files:
            relative = Path(item.relative_path)
            parent_id = project_id
            current = Path()

            for part in relative.parts[:-1]:
                current = current / part
                folder_rel = current.as_posix()
                folder_id = f"folder:{folder_rel}"
                if folder_id not in folder_ids:
                    graph.add_node(
                        Node(
                            id=folder_id,
                            kind="Folder",
                            label=part,
                            attributes={"path": folder_rel},
                        )
                    )
                    graph.add_edge(Edge(parent_id, folder_id, "contains"))
                    folder_ids.add(folder_id)
                parent_id = folder_id

            file_id = f"file:{item.relative_path}"
            graph.add_node(
                Node(
                    id=file_id,
                    kind="File",
                    label=relative.name,
                    attributes={
                        "path": item.relative_path,
                        "extension": relative.suffix.lower(),
                        "size_bytes": item.size_bytes,
                        "modified_ns": item.modified_ns,
                    },
                )
            )
            graph.add_edge(Edge(parent_id, file_id, "contains"))

        result = ProjectIndexResult(
            project_id=project_id,
            files_indexed=len(files),
            folders_indexed=len(folder_ids),
            nodes_total=len(graph.nodes),
            edges_total=len(graph.edges),
        )
        return graph, result
