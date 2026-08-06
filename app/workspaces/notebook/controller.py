from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


NOTEBOOK_CATEGORIES = {
    "Идеи": "ideas",
    "ADR": "adr",
    "Исследования": "research",
    "Решения": "decisions",
    "Задачи": "tasks",
    "Встречи": "meetings",
    "Черновики": "drafts",
}


@dataclass(frozen=True)
class NotebookDocument:
    path: Path
    category: str
    title: str
    content: str


class EngineeringNotebookController:
    """Управляет файловым Engineering Notebook внутри каталога .devhub."""

    def __init__(self) -> None:
        self.project_root: Path | None = None

    @property
    def notebook_root(self) -> Path | None:
        if self.project_root is None:
            return None
        return self.project_root / ".devhub"

    def set_project(self, project_root: Path) -> None:
        root = project_root.resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("Папка проекта недоступна")
        self.project_root = root
        self.ensure_structure()

    def ensure_structure(self) -> None:
        root = self.notebook_root
        if root is None:
            raise RuntimeError("Проект не выбран")
        root.mkdir(parents=True, exist_ok=True)
        for folder in NOTEBOOK_CATEGORIES.values():
            (root / folder).mkdir(parents=True, exist_ok=True)

    def list_documents(self, category: str) -> list[Path]:
        directory = self._category_dir(category)
        return sorted(directory.glob("*.md"), key=lambda path: path.stat().st_mtime, reverse=True)

    def create_document(self, category: str, title: str) -> NotebookDocument:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Название документа не заполнено")
        directory = self._category_dir(category)
        slug = self._slugify(clean_title)
        path = self._unique_path(directory / f"{slug}.md")
        now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        content = f"# {clean_title}\n\nСоздано: {now}\n\n"
        path.write_text(content, encoding="utf-8")
        return NotebookDocument(path=path, category=category, title=clean_title, content=content)

    def load_document(self, path: Path) -> NotebookDocument:
        resolved = path.resolve()
        root = self.notebook_root
        if root is None or root.resolve() not in resolved.parents:
            raise ValueError("Документ находится вне Engineering Notebook")
        content = resolved.read_text(encoding="utf-8", errors="replace")
        title = self._extract_title(content) or resolved.stem
        category = self._category_from_path(resolved)
        return NotebookDocument(path=resolved, category=category, title=title, content=content)

    def save_document(self, path: Path, content: str) -> NotebookDocument:
        document = self.load_document(path)
        path.write_text(content, encoding="utf-8")
        title = self._extract_title(content) or document.title
        return NotebookDocument(path=path, category=document.category, title=title, content=content)

    def delete_document(self, path: Path) -> None:
        document = self.load_document(path)
        document.path.unlink()

    def _category_dir(self, category: str) -> Path:
        root = self.notebook_root
        if root is None:
            raise RuntimeError("Проект не выбран")
        folder = NOTEBOOK_CATEGORIES.get(category)
        if folder is None:
            raise ValueError(f"Неизвестная категория: {category}")
        directory = root / folder
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _category_from_path(self, path: Path) -> str:
        for title, folder in NOTEBOOK_CATEGORIES.items():
            if path.parent.name == folder:
                return title
        return "Черновики"

    @staticmethod
    def _extract_title(content: str) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = value.lower().replace("ё", "е")
        normalized = re.sub(r"[^a-zа-я0-9]+", "-", normalized, flags=re.IGNORECASE)
        return normalized.strip("-") or "document"

    @staticmethod
    def _unique_path(path: Path) -> Path:
        if not path.exists():
            return path
        index = 2
        while True:
            candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
            if not candidate.exists():
                return candidate
            index += 1
