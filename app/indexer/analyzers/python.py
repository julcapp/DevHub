from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PythonSymbol:
    kind: str
    name: str
    qualified_name: str
    line: int


@dataclass(frozen=True)
class PythonAnalysis:
    module: str
    symbols: tuple[PythonSymbol, ...]
    imports: tuple[str, ...]


class PythonAnalyzer:
    """Извлекает классы, функции и импорты из Python-файла через AST."""

    def analyze(self, path: Path, root: Path) -> PythonAnalysis:
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            raise ValueError(f"Ошибка синтаксиса Python в {path.name}: {error.msg}") from error

        relative = path.resolve().relative_to(root.resolve())
        module = self._module_name(relative)
        symbols: list[PythonSymbol] = []
        imports: list[str] = []

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(self._import_names(node))
            elif isinstance(node, ast.ClassDef):
                symbols.append(
                    PythonSymbol(
                        kind="Class",
                        name=node.name,
                        qualified_name=f"{module}.{node.name}",
                        line=node.lineno,
                    )
                )
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append(
                            PythonSymbol(
                                kind="Method",
                                name=child.name,
                                qualified_name=f"{module}.{node.name}.{child.name}",
                                line=child.lineno,
                            )
                        )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(
                    PythonSymbol(
                        kind="Function",
                        name=node.name,
                        qualified_name=f"{module}.{node.name}",
                        line=node.lineno,
                    )
                )

        return PythonAnalysis(
            module=module,
            symbols=tuple(symbols),
            imports=tuple(dict.fromkeys(imports)),
        )

    @staticmethod
    def _module_name(relative: Path) -> str:
        without_suffix = relative.with_suffix("")
        parts = list(without_suffix.parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    @staticmethod
    def _import_names(node: ast.Import | ast.ImportFrom) -> list[str]:
        if isinstance(node, ast.Import):
            return [alias.name for alias in node.names]

        prefix = "." * node.level
        if node.module:
            return [prefix + node.module]

        if node.level:
            return [prefix + alias.name for alias in node.names]
        return []
