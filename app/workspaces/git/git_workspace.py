from __future__ import annotations

from pathlib import Path
from time import perf_counter

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.workspaces.git.controller import GitWorkspaceController
from app.workspaces.git.git_operation_task import GitOperationTask
from app.workspaces.git.git_toolbar import GitToolbarWidget
from app.workspaces.git.project_card import ProjectCardWidget
from app.workspaces.git.repository_list import RepositoryListWidget


class GitWorkspace(QWidget):
    """Рабочее пространство локальных Git-репозиториев."""

    repository_selected = Signal(Path)

    def __init__(self) -> None:
        super().__init__()
        self.controller = GitWorkspaceController()
        self.repository_list = RepositoryListWidget()
        self.project_card = ProjectCardWidget()
        self.git_toolbar = GitToolbarWidget()
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Журнал Git Workspace")
        self.selected_repository: Path | None = None
        self.current_task: GitOperationTask | None = None
        self._build_ui()
        self._bind_events()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        heading_row = QHBoxLayout()
        heading = QLabel("Разработка → Git")
        heading.setObjectName("WorkspaceTitle")
        self.scan_button = QPushButton("Найти репозитории")
        self.scan_button.clicked.connect(self.scan_repositories)
        heading_row.addWidget(heading)
        heading_row.addStretch()
        heading_row.addWidget(self.scan_button)

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
        layout.addWidget(self.git_toolbar)
        layout.addWidget(content, 1)
        layout.addWidget(QLabel("Журнал операций"))
        layout.addWidget(self.output)

    def _bind_events(self) -> None:
        self.repository_list.repository_selected.connect(self._select_repository)
        self.git_toolbar.fetch_requested.connect(lambda: self._start_operation("fetch"))
        self.git_toolbar.pull_requested.connect(lambda: self._start_operation("pull"))
        self.git_toolbar.push_requested.connect(lambda: self._start_operation("push"))
        self.git_toolbar.commit_requested.connect(self._request_commit)
        self.git_toolbar.history_requested.connect(lambda: self._start_operation("history"))

    def scan_repositories(self) -> None:
        started = perf_counter()
        self.output.append("Поиск локальных Git-репозиториев...")
        self.scan_button.setEnabled(False)
        try:
            rows = self.controller.scan()
        except Exception as error:  # UI boundary: показываем диагностическую ошибку пользователю.
            self.output.append(f"Ошибка сканирования: {error}")
            QMessageBox.critical(self, "Ошибка сканирования", str(error))
            return
        finally:
            self.scan_button.setEnabled(True)
        self.repository_list.set_repositories(rows)
        duration = perf_counter() - started
        self.output.append(f"Найдено репозиториев: {len(rows)}. Время: {duration:.2f} сек.")

    def _select_repository(self, repository: Path) -> None:
        self.selected_repository = repository
        self.project_card.show_repository(repository)
        self.git_toolbar.setEnabled(True)
        self.repository_selected.emit(repository)
        self.output.append(f"Выбран проект: {repository.name}")

    def _request_commit(self) -> None:
        message, accepted = QInputDialog.getText(
            self,
            "Создание Commit",
            "Введите сообщение Commit:",
        )
        if accepted:
            self._start_operation("commit", message)

    def _start_operation(self, operation: str, commit_message: str = "") -> None:
        if self.selected_repository is None:
            QMessageBox.warning(self, "DevHub", "Сначала выберите репозиторий.")
            return
        if self.current_task is not None and self.current_task.isRunning():
            QMessageBox.information(self, "DevHub", "Другая Git-операция уже выполняется.")
            return
        try:
            commands = self.controller.operation_commands(operation, commit_message)
        except ValueError as error:
            QMessageBox.warning(self, "DevHub", str(error))
            return

        self.output.append("")
        self.output.append("=" * 70)
        self.output.append(f"Проект: {self.selected_repository.name} | Операция: {operation}")
        self.git_toolbar.set_busy(True)
        self.scan_button.setEnabled(False)

        task = GitOperationTask(self.selected_repository, commands, self)
        self.current_task = task
        task.progress.connect(self.output.append)
        task.result_ready.connect(self._show_result)
        task.finished_success.connect(lambda: self._finish_operation(True, operation))
        task.finished_error.connect(self._operation_error)
        task.finished.connect(self._cleanup_task)
        task.start()

    def _show_result(self, result) -> None:
        for line in result.messages:
            self.output.append(str(line))

    def _finish_operation(self, success: bool, operation: str) -> None:
        status = "успешно" if success else "с ошибкой"
        self.output.append(f"Операция {operation} завершена {status}.")
        if operation != "history" and self.selected_repository is not None:
            self.project_card.show_repository(self.selected_repository)

    def _operation_error(self, error_text: str) -> None:
        self.output.append(f"Ошибка: {error_text}")
        QMessageBox.critical(self, "Ошибка Git", error_text)

    def _cleanup_task(self) -> None:
        self.git_toolbar.set_busy(False)
        self.scan_button.setEnabled(True)
        self.current_task = None
