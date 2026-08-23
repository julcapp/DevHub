from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from app.workspaces.explorer.controller import IGNORED_DIRECTORIES, ProjectExplorerController
from app.workspaces.explorer.document_viewer import DocumentViewer


class ProjectExplorerWorkspace(QWidget):
    """Проводник локального инженерного проекта и просмотрщик файлов."""

    file_selected = Signal(Path)

    def __init__(self) -> None:
        super().__init__()
        self.controller = ProjectExplorerController()
        self.root_path: Path | None = None
        self.model = QFileSystemModel(self)
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        self.model.setNameFilterDisables(False)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(False)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, 0)
        self.tree.doubleClicked.connect(self._open_index)
        self.viewer = DocumentViewer()
        self.path_label = QLabel("Проект не выбран")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Фильтр по имени файла...")
        self.search.textChanged.connect(self._apply_filter)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Проводник проекта")
        title.setObjectName("WorkspaceTitle")
        choose_button = QPushButton("Открыть проект")
        choose_button.clicked.connect(self.choose_project)
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.refresh)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(choose_button)
        header.addWidget(refresh_button)

        splitter = QSplitter()
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.path_label)
        left_layout.addWidget(self.search)
        left_layout.addWidget(self.tree, 1)
        splitter.addWidget(left)
        splitter.addWidget(self.viewer)
        splitter.setSizes([480, 900])

        layout.addLayout(header)
        layout.addWidget(splitter, 1)

    def choose_project(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if directory:
            self.set_project(Path(directory))

    def set_project(self, root_path: Path) -> None:
        root_path = root_path.resolve()
        if not root_path.exists() or not root_path.is_dir():
            self.viewer.clear_preview("Папка проекта недоступна")
            return
        self.root_path = root_path
        root_index = self.model.setRootPath(str(root_path))
        self.tree.setRootIndex(root_index)
        self.tree.setColumnWidth(0, 320)
        self.path_label.setText(str(root_path))
        self.viewer.clear_preview("Выберите поддерживаемый файл в дереве проекта")
        self._hide_ignored_directories(root_index)

    def refresh(self) -> None:
        if self.root_path is not None:
            self.set_project(self.root_path)

    def _hide_ignored_directories(self, root_index: QModelIndex) -> None:
        for row in range(self.model.rowCount(root_index)):
            index = self.model.index(row, 0, root_index)
            if self.model.fileName(index) in IGNORED_DIRECTORIES:
                self.tree.setRowHidden(row, root_index, True)

    def _apply_filter(self, text: str) -> None:
        patterns = [f"*{text}*"] if text.strip() else []
        self.model.setNameFilters(patterns)

    def _open_index(self, index: QModelIndex) -> None:
        path = Path(self.model.filePath(index))
        if path.is_dir():
            self._hide_ignored_directories(index)
            return
        try:
            preview = self.controller.preview(path)
        except (FileNotFoundError, ValueError, OSError) as error:
            self.viewer.clear_preview(str(error))
            return
        self.viewer.show_preview(preview)
        self.file_selected.emit(path)
