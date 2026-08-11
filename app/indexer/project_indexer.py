from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.indexer.analyzers import PythonAnalyzer
from app.indexer.file_scanner import FileScanner
from app.knowledge import Edge, KnowledgeGraph, Node


@dataclass(frozen=True)
class ProjectIndexResult:
    project_id: str
    files_indexed: int
    folders_indexed: int
    nodes_total: int
    edges_total: int
    python_files_analyzed: int = 0
    symbols_indexed: int = 0
    imports_indexed: int = 0


class ProjectIndexer:
    """Строит инженерный граф структуры проекта и Python-символов."""

    def __init__(
        self,
        scanner: FileScanner | None = None,
        python_analyzer: PythonAnalyzer | None = None,
    ) -> None:
        self.scanner = scanner or FileScanner()
        self.python_analyzer = python_analyzer or PythonAnalyzer()

    def build_graph(
        self,
        root: Path,
        graph: KnowledgeGraph | None = None,
    ) -> tuple[KnowledgeGraph, ProjectIndexResult]:
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
        python_files_analyzed = 0
        symbols_indexed = 0
        imports_indexed = 0

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

            if relative.suffix.lower() == ".py":
                absolute_path = root / relative
                try:
                    analysis = self.python_analyzer.analyze(absolute_path, root)
                except (OSError, ValueError):
                    continue
                python_files_analyzed += 1

                module_id = f"module:{analysis.module or relative.stem}"
                graph.add_node(
                    Node(
                        id=module_id,
                        kind="Module",
                        label=analysis.module or relative.stem,
                        attributes={"path": item.relative_path},
                    )
                )
                graph.add_edge(Edge(file_id, module_id, "defines"))

                for symbol in analysis.symbols:
                    symbol_id = f"symbol:{symbol.qualified_name}"
                    graph.add_node(
                        Node(
                            id=symbol_id,
                            kind=symbol.kind,
                            label=symbol.name,
                            attributes={
                                "qualified_name": symbol.qualified_name,
                                "line": symbol.line,
                                "file": item.relative_path,
                            },
                        )
                    )
                    graph.add_edge(Edge(module_id, symbol_id, "defines"))
                    symbols_indexed += 1

                for imported_module in analysis.imports:
                    import_id = f"module-ref:{imported_module}"
                    graph.add_node(
                        Node(
                            id=import_id,
                            kind="ModuleReference",
                            label=imported_module,
                            attributes={},
                        )
                    )
                    graph.add_edge(Edge(module_id, import_id, "imports"))
                    imports_indexed += 1

        result = ProjectIndexResult(
            project_id=project_id,
            files_indexed=len(files),
            folders_indexed=len(folder_ids),
            nodes_total=len(graph.nodes),
            edges_total=len(graph.edges),
            python_files_analyzed=python_files_analyzed,
            symbols_indexed=symbols_indexed,
            imports_indexed=imports_indexed,
        )
        return graph, result
