from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.workspaces.notebook.controller import (
    NOTEBOOK_CATEGORIES,
    EngineeringNotebookController,
)


class EngineeringNotebookWorkspace(QWidget):
    """Инженерный журнал проекта: идеи, ADR, решения, задачи и исследования."""

    def __init__(self) -> None:
        super().__init__()
        self.controller = EngineeringNotebookController()
        self.current_document: Path | None = None
        self.project_label = QLabel("Проект не выбран")
        self.categories = QListWidget()
        self.documents = QListWidget()
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Выберите или создайте документ")
        self.save_button = QPushButton("Сохранить")
        self.delete_button = QPushButton("Удалить")
        self._build_ui()
        self._populate_categories()
        self.categories.currentTextChanged.connect(self._reload_documents)
        self.documents.itemSelectionChanged.connect(self._open_selected_document)
        self.save_button.clicked.connect(self.save_current_document)
        self.delete_button.clicked.connect(self.delete_current_document)
        self._update_controls()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Инженерный журнал")
        title.setObjectName("WorkspaceTitle")
        choose_button = QPushButton("Открыть проект")
        choose_button.clicked.connect(self.choose_project)
        new_button = QPushButton("Новый документ")
        new_button.clicked.connect(self.create_document)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(choose_button)
        header.addWidget(new_button)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        category_panel = QWidget()
        category_layout = QVBoxLayout(category_panel)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.addWidget(self.project_label)
        category_layout.addWidget(QLabel("Разделы"))
        category_layout.addWidget(self.categories, 1)

        document_panel = QWidget()
        document_layout = QVBoxLayout(document_panel)
        document_layout.setContentsMargins(0, 0, 0, 0)
        document_layout.addWidget(QLabel("Документы"))
        document_layout.addWidget(self.documents, 1)

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(QLabel("Редактор Markdown"))
        editor_layout.addWidget(self.editor, 1)
        editor_actions = QHBoxLayout()
        editor_actions.addStretch()
        editor_actions.addWidget(self.delete_button)
        editor_actions.addWidget(self.save_button)
        editor_layout.addLayout(editor_actions)

        splitter.addWidget(category_panel)
        splitter.addWidget(document_panel)
        splitter.addWidget(editor_panel)
        splitter.setSizes([220, 320, 760])

        layout.addLayout(header)
        layout.addWidget(splitter, 1)

    def _populate_categories(self) -> None:
        self.categories.clear()
        for title in NOTEBOOK_CATEGORIES:
            self.categories.addItem(title)
        self.categories.setCurrentRow(0)

    def choose_project(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if directory:
            self.set_project(Path(directory))

    def set_project(self, project_root: Path) -> None:
        try:
            self.controller.set_project(project_root)
        except ValueError as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            return
        self.project_label.setText(str(project_root.resolve()))
        self.current_document = None
        self.editor.clear()
        self._reload_documents(self.categories.currentItem().text() if self.categories.currentItem() else "Идеи")
        self._update_controls()

    def create_document(self) -> None:
        if self.controller.project_root is None:
            QMessageBox.information(self, "Engineering Notebook", "Сначала выберите проект")
            return
        category = self.categories.currentItem().text() if self.categories.currentItem() else "Идеи"
        title, accepted = QInputDialog.getText(self, "Новый документ", "Название:")
        if not accepted:
            return
        try:
            document = self.controller.create_document(category, title)
        except (RuntimeError, ValueError, OSError) as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            return
        self._reload_documents(category)
        self._select_document(document.path)

    def save_current_document(self) -> None:
        if self.current_document is None:
            return
        try:
            self.controller.save_document(self.current_document, self.editor.toPlainText())
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            return
        self._reload_documents(self.categories.currentItem().text() if self.categories.currentItem() else "Идеи")
        self._select_document(self.current_document)

    def delete_current_document(self) -> None:
        if self.current_document is None:
            return
        answer = QMessageBox.question(
            self,
            "Удаление документа",
            f"Удалить {self.current_document.name}?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controller.delete_document(self.current_document)
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            return
        self.current_document = None
        self.editor.clear()
        self._reload_documents(self.categories.currentItem().text() if self.categories.currentItem() else "Идеи")
        self._update_controls()

    def _reload_documents(self, category: str) -> None:
        self.documents.clear()
        if self.controller.project_root is None:
            return
        try:
            paths = self.controller.list_documents(category)
        except (RuntimeError, ValueError, OSError):
            return
        for path in paths:
            item = QListWidgetItem(path.stem)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.documents.addItem(item)

    def _open_selected_document(self) -> None:
        item = self.documents.currentItem()
        if item is None:
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        try:
            document = self.controller.load_document(path)
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            return
        self.current_document = document.path
        self.editor.setPlainText(document.content)
        self._update_controls()

    def _select_document(self, path: Path) -> None:
        for index in range(self.documents.count()):
            item = self.documents.item(index)
            if Path(item.data(Qt.ItemDataRole.UserRole)) == path:
                self.documents.setCurrentItem(item)
                return

    def _update_controls(self) -> None:
        enabled = self.current_document is not None
        self.editor.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)
