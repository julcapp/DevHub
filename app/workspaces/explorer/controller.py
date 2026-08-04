from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".ini",
    ".cfg",
    ".py",
    ".gitignore",
}

SPECIAL_TEXT_FILES = {"LICENSE", "Dockerfile", "Makefile", ".env.example"}


@dataclass(frozen=True)
class FilePreview:
    path: Path
    content: str
    size_bytes: int
    line_count: int
    kind: str


class ProjectExplorerController:
    """Читает дерево и файлы проекта без зависимости от Qt."""

    def is_visible(self, path: Path) -> bool:
        return path.name not in IGNORED_DIRECTORIES

    def list_children(self, directory: Path) -> list[Path]:
        if not directory.exists() or not directory.is_dir():
            return []
        try:
            children = [path for path in directory.iterdir() if self.is_visible(path)]
        except OSError:
            return []
        return sorted(children, key=lambda path: (not path.is_dir(), path.name.lower()))

    def can_preview(self, path: Path) -> bool:
        return path.is_file() and (
            path.suffix.lower() in TEXT_EXTENSIONS or path.name in SPECIAL_TEXT_FILES
        )

    def preview(self, path: Path, max_bytes: int = 1_000_000) -> FilePreview:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(path)
        if not self.can_preview(path):
            raise ValueError(f"Формат файла не поддерживается: {path.name}")
        size = path.stat().st_size
        if size > max_bytes:
            raise ValueError(f"Файл слишком большой для просмотра: {size} байт")

        content = path.read_text(encoding="utf-8", errors="replace")
        kind = path.suffix.lower().lstrip(".") or path.name
        if path.suffix.lower() == ".json":
            try:
                content = json.dumps(json.loads(content), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
        return FilePreview(
            path=path,
            content=content,
            size_bytes=size,
            line_count=len(content.splitlines()),
            kind=kind,
        )
