from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    ".devhub",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".cache",
    ".pytest_cache",
}

INDEXABLE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".xml",
    ".sql",
    ".toml",
    ".ini",
    ".cfg",
    ".html",
    ".css",
}

INDEXABLE_SPECIAL_FILES = {"Dockerfile", "Makefile", "LICENSE", ".gitignore"}


@dataclass(frozen=True)
class ScannedFile:
    path: Path
    relative_path: str
    size_bytes: int
    modified_ns: int


class FileScanner:
    """Сканирует индексируемые файлы проекта без зависимости от UI."""

    def is_ignored_directory(self, path: Path) -> bool:
        return path.name in IGNORED_DIRECTORIES

    def is_indexable_file(self, path: Path) -> bool:
        return path.is_file() and (
            path.suffix.lower() in INDEXABLE_EXTENSIONS or path.name in INDEXABLE_SPECIAL_FILES
        )

    def scan(self, root: Path) -> list[ScannedFile]:
        root = root.resolve()
        if not root.exists() or not root.is_dir():
            return []

        results: list[ScannedFile] = []
        for path in root.rglob("*"):
            if any(part in IGNORED_DIRECTORIES for part in path.relative_to(root).parts):
                continue
            if not self.is_indexable_file(path):
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            results.append(
                ScannedFile(
                    path=path,
                    relative_path=path.relative_to(root).as_posix(),
                    size_bytes=stat.st_size,
                    modified_ns=stat.st_mtime_ns,
                )
            )
        return sorted(results, key=lambda item: item.relative_path.lower())
