from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton,
    QSplitter, QTextEdit, QVBoxLayout, QWidget,
)


class ResearchStatus(str, Enum):
    NEW = "Не изучено"
    REVIEW = "Изучаем"
    CANDIDATE = "Кандидат"
    ADOPTED = "Принято"
    REJECTED = "Отклонено"


@dataclass(slots=True)
class StarredRepository:
    full_name: str
    description: str = ""
    url: str = ""
    language: str = ""
    license_name: str = ""
    status: ResearchStatus = ResearchStatus.NEW
    notes: str = ""


class StarsWorkspace(QWidget):
    """Библиотека GitHub Stars: источники для исследования, а не подключённый код."""

    def __init__(self) -> None:
        super().__init__()
        self._repositories: list[StarredRepository] = []
        self._store = None
        self._build_ui()
        self._load_local()

    def _load_local(self) -> None:
        from app.workspaces.stars.store import StarsStore
        self._store = StarsStore()
        self._repositories = list(self._store.load().values())
        self._apply_filter()
        if self._repositories:
            self.state_label.setText(f"Локально сохранено карточек: {len(self._repositories)}.")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        heading = QLabel("Звёздочки")
        heading.setObjectName("WorkspaceTitle")
        description = QLabel(
            "GitHub-репозитории, отмеченные Star: библиотека технологий и идей "
            "для исследования перед принятием решения об использовании."
        )
        description.setWordWrap(True)
        description.setObjectName("WorkspaceDescription")

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по звёздочкам")
        self.sync_button = QPushButton("Синхронизировать с GitHub")
        self.sync_button.setToolTip("Подключение GitHub Stars будет активировано через сервис синхронизации.")
        self.sync_button.clicked.connect(self._sync_requested)
        toolbar.addWidget(self.search, 1)
        toolbar.addWidget(self.sync_button)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._show_repository)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        self.name_label = QLabel("Выберите репозиторий")
        self.name_label.setObjectName("PanelTitle")
        self.meta_label = QLabel("")
        self.meta_label.setWordWrap(True)
        self.status_combo = QComboBox()
        self.status_combo.addItems([status.value for status in ResearchStatus])
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Наши заметки и выводы по репозиторию")
        self.save_button = QPushButton("Сохранить карточку")
        self.save_button.clicked.connect(self._save_card)
        detail_layout.addWidget(self.name_label)
        detail_layout.addWidget(self.meta_label)
        detail_layout.addWidget(QLabel("Статус исследования"))
        detail_layout.addWidget(self.status_combo)
        detail_layout.addWidget(QLabel("Заметки"))
        detail_layout.addWidget(self.notes, 1)
        detail_layout.addWidget(self.save_button)

        splitter.addWidget(self.list_widget)
        splitter.addWidget(detail)
        splitter.setStretchFactor(1, 1)

        self.state_label = QLabel(
            "Локальная библиотека готова. GitHub Stars пока не синхронизированы."
        )
        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addLayout(toolbar)
        layout.addWidget(splitter, 1)
        layout.addWidget(self.state_label)

        self.search.textChanged.connect(self._apply_filter)

    def set_repositories(self, repositories: list[StarredRepository]) -> None:
        self._repositories = repositories
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self.search.text().strip().lower()
        self.list_widget.clear()
        for index, repo in enumerate(self._repositories):
            haystack = f"{repo.full_name} {repo.description} {repo.language}".lower()
            if query and query not in haystack:
                continue
            self.list_widget.addItem(repo.full_name)
            self.list_widget.item(self.list_widget.count() - 1).setData(Qt.ItemDataRole.UserRole, index)

    def _current_repository(self) -> StarredRepository | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return self._repositories[int(item.data(Qt.ItemDataRole.UserRole))]

    def _show_repository(self, _: int) -> None:
        repo = self._current_repository()
        if repo is None:
            return
        self.name_label.setText(repo.full_name)
        meta = [value for value in (repo.language, repo.license_name, repo.url) if value]
        self.meta_label.setText(" · ".join(meta) + ("\n" + repo.description if repo.description else ""))
        self.status_combo.setCurrentText(repo.status.value)
        self.notes.setPlainText(repo.notes)

    def _save_card(self) -> None:
        repo = self._current_repository()
        if repo is None:
            self.state_label.setText("Сначала выберите репозиторий.")
            return
        repo.status = ResearchStatus(self.status_combo.currentText())
        repo.notes = self.notes.toPlainText().strip()
        if self._store is not None:
            self._store.save(self._repositories)
        self.state_label.setText(f"Карточка {repo.full_name} обновлена локально.")

    def _sync_requested(self) -> None:
        self.state_label.setText(
            "Сервис GitHub Stars ещё не авторизован. Локальные заметки не будут перезаписаны при синхронизации."
        )
