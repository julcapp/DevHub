from __future__ import annotations

from pathlib import Path
from time import perf_counter

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.workspaces.git.controller import GitWorkspaceController
from app.workspaces.git.project_card import ProjectCardWidget
from app.workspaces.git.repository_list import RepositoryListWidget


class GitWorkspace(QWidget):
    """Первое рабочее пространство разработки: локальные Git-репозитории."""

    repository_selected = Signal(Path)

    def __init__(self) -> None:
        super().__init__()
        self.controller = GitWorkspaceController()
        self.repository_list = RepositoryListWidget()
        self.project_card = ProjectCardWidget()
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Журнал Git Workspace")
        self._build_ui()
        self.repository_list.repository_selected.connect(self._select_repository)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        heading_row = QHBoxLayout()
        heading = QLabel("Разработка → Git")
        heading.setObjectName("WorkspaceTitle")
        scan_button = QPushButton("Найти репозитории")
        scan_button.clicked.connect(self.scan_repositories)
        heading_row.addWidget(heading)
        heading_row.addStretch()
        heading_row.addWidget(scan_button)

        content = QSplitter()
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Реестр проектов"))
        left_layout.addWidget(self.repository_list)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("Паспорт проекта"))
        right_layout.addWidget(self.project_card)

        content.addWidget(left)
        content.addWidget(right)
        content.setSizes([850, 420])

        layout.addLayout(heading_row)
        layout.addWidget(content, 1)
        layout.addWidget(QLabel("Журнал операций"))
        layout.addWidget(self.output)

    def scan_repositories(self) -> None:
        started = perf_counter()
        self.output.append("Поиск локальных Git-репозиториев...")
        try:
            rows = self.controller.scan()
        except Exception as error:  # UI boundary: показываем диагностическую ошибку пользователю.
            self.output.append(f"Ошибка сканирования: {error}")
            return
        self.repository_list.set_repositories(rows)
        duration = perf_counter() - started
        self.output.append(f"Найдено репозиториев: {len(rows)}. Время: {duration:.2f} сек.")

    def _select_repository(self, repository: Path) -> None:
        self.project_card.show_repository(repository)
        self.repository_selected.emit(repository)
        self.output.append(f"Выбран проект: {repository.name}")
