from pathlib import Path
from datetime import datetime
from time import perf_counter

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QSplitter,
    QStatusBar,
    QMessageBox
)

from app.config import load_settings
from app.devadvisor_window import DevAdvisorWindow
from app.git_manager import (
    detect_sync_state,
    find_repositories,
    format_result,
    format_summary,
    get_branch,
    get_local_last_commit_date,
    get_remote_last_commit_date,
    run_repository_command,
    sync_all_repositories
)
from app.project_metadata import load_project_metadata
from app.workers.git_task import GitTask


SYNC_STATE_RU = {
    "SYNCED": "Синхронизировано",
    "PULL_REQUIRED": "Есть изменения на GitHub",
    "PUSH_REQUIRED": "Нужно отправить изменения",
    "COMMIT_REQUIRED": "Требуется Commit",
    "DIVERGED": "Есть расхождения",
    "UNKNOWN": "Неизвестно",
    "ERROR": "Ошибка"
}


def translate_sync_state(state: str) -> str:
    return SYNC_STATE_RU.get(state, state)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DevHub v0.5 Alpha — Ваш центр управления инженерными проектами")
        self.resize(1450, 850)

        self.settings = load_settings()
        self.repositories: list[Path] = []
        self.selected_repo: Path | None = None
        self.devadvisor_window: DevAdvisorWindow | None = None
        self.current_git_task = None
        self.started_at = datetime.now()

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        root_layout = QVBoxLayout()

        header = QLabel("DevHub v0.5 Alpha — Ваш центр управления инженерными проектами")
        header.setObjectName("HeaderLabel")

        self.runtime_label = QLabel()
        self.runtime_label.setObjectName("RuntimeLabel")
        self.runtime_label.setToolTip(
            "Время запуска текущей сессии DevHub и продолжительность работы приложения."
        )

        self.runtime_timer = QTimer(self)
        self.runtime_timer.timeout.connect(self.update_runtime_label)
        self.runtime_timer.start(1000)
        self.update_runtime_label()

        header_layout = QHBoxLayout()
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.runtime_label)

        toolbar_layout = QHBoxLayout()

        self.scan_button = QPushButton("Найти репозитории")
        self.sync_button = QPushButton("Синхронизировать всё")
        self.fetch_button = QPushButton("Проверить изменения")
        self.pull_button = QPushButton("Получить изменения")
        self.push_button = QPushButton("Отправить изменения")
        self.advisor_button = QPushButton("Открыть DevAdvisor")
        self.clear_log_button = QPushButton("Очистить журнал")

        self.scan_button.setToolTip(
            "Ищет Git-репозитории в рабочей папке, указанной в настройках DevHub."
        )
        self.sync_button.setToolTip(
            "Выполняет безопасную синхронизацию всех найденных репозиториев согласно настройкам."
        )
        self.fetch_button.setToolTip(
            "Проверяет наличие новых изменений в удалённом репозитории без изменения локальных файлов."
        )
        self.pull_button.setToolTip(
            "Загружает изменения из GitHub в выбранный локальный репозиторий."
        )
        self.push_button.setToolTip(
            "Отправляет ваши локальные Commit в удалённый репозиторий GitHub."
        )
        self.advisor_button.setToolTip(
            "Открывает отдельное рабочее пространство DevAdvisor для инженерного анализа проекта."
        )
        self.clear_log_button.setToolTip(
            "Очищает журнал операций в текущем окне DevHub."
        )

        self.scan_button.clicked.connect(self.scan_repositories)
        self.sync_button.clicked.connect(self.sync_all)
        self.fetch_button.clicked.connect(lambda: self.run_selected_git_command(["fetch", "--prune"]))
        self.pull_button.clicked.connect(lambda: self.run_selected_git_command(["pull"]))
        self.push_button.clicked.connect(lambda: self.run_selected_git_command(["push"]))
        self.advisor_button.clicked.connect(self.open_devadvisor)
        self.clear_log_button.clicked.connect(self.clear_log)

        for button in [
            self.scan_button,
            self.sync_button,
            self.fetch_button,
            self.pull_button,
            self.push_button,
            self.advisor_button,
            self.clear_log_button
        ]:
            toolbar_layout.addWidget(button)

        self.repo_table = QTableWidget()
        self.repo_table.setColumnCount(9)
        self.repo_table.setHorizontalHeaderLabels([
            "Проект",
            "Ветка",
            "Состояние",
            "Локально",
            "GitHub",
            "Версия",
            "Статус",
            "Описание",
            "Путь"
        ])
        self.repo_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.repo_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.repo_table.itemSelectionChanged.connect(self.on_repository_selected)
        self.repo_table.setToolTip(
            "Реестр проектов DevHub. Выберите строку, чтобы открыть паспорт проекта и доступные действия."
        )

        widths = [180, 80, 190, 180, 180, 100, 110, 460, 380]
        for index, width in enumerate(widths):
            self.repo_table.setColumnWidth(index, width)

        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Реестр проектов"))
        left_layout.addWidget(self.repo_table)
        left_panel.setLayout(left_layout)

        self.project_info = QTextEdit()
        self.project_info.setReadOnly(True)
        self.project_info.setText("Выберите репозиторий в таблице.")
        self.project_info.setToolTip(
            "Паспорт выбранного проекта: метаданные DHMS, описание, путь и доступные действия."
        )

        center_panel = QWidget()
        center_layout = QVBoxLayout()
        center_layout.addWidget(QLabel("Паспорт проекта"))
        center_layout.addWidget(self.project_info)
        center_panel.setLayout(center_layout)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(10)
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.setSizes([970, 420])

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setToolTip(
            "Журнал технических операций: поиск репозиториев, Git-команды, синхронизация и ошибки."
        )

        log_panel = QWidget()
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("Журнал операций"))
        log_layout.addWidget(self.log_output)
        log_panel.setLayout(log_layout)

        vertical_splitter = QSplitter(Qt.Vertical)
        vertical_splitter.setHandleWidth(10)
        vertical_splitter.addWidget(main_splitter)
        vertical_splitter.addWidget(log_panel)
        vertical_splitter.setSizes([590, 260])

        root_layout.addLayout(header_layout)
        root_layout.addLayout(toolbar_layout)
        root_layout.addWidget(vertical_splitter)

        central_widget.setLayout(root_layout)
        self.setCentralWidget(central_widget)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("DevHub готов к работе")

        self.apply_style()

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }

            QLabel#HeaderLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
            }

            QLabel#RuntimeLabel {
                font-size: 12px;
                font-weight: normal;
                padding: 8px;
                color: #404040;
            }

            QLabel {
                font-weight: bold;
            }

            QPushButton {
                padding: 8px;
                font-size: 13px;
            }

            QTextEdit, QTableWidget {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
                font-family: Consolas, Arial;
                font-size: 12px;
            }

            QHeaderView::section {
                background-color: #eeeeee;
                padding: 6px;
                border: 1px solid #b0b0b0;
                font-weight: bold;
            }

            QSplitter::handle {
                background-color: #b0b0b0;
            }

            QSplitter::handle:hover {
                background-color: #808080;
            }
        """)

    def update_runtime_label(self):
        elapsed = datetime.now() - self.started_at
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        started_text = self.started_at.strftime("%d.%m.%Y %H:%M:%S")
        uptime_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.runtime_label.setText(
            f"Запуск: {started_text} | Время работы: {uptime_text}"
        )

    def write_log(self, text: str):
        self.log_output.append(text)

    def clear_log(self):
        self.log_output.clear()
        self.statusBar().showMessage("Журнал очищен")

    def scan_repositories(self):
        total_start = perf_counter()

        self.repo_table.setRowCount(0)
        self.selected_repo = None

        self.write_log("")
        self.write_log("=" * 70)
        self.write_log("EDP-0005.1 | Repository Scan Diagnostics")
        self.write_log("=" * 70)

        workspace_start = perf_counter()
        self.repositories = find_repositories(
            workspace_paths=self.settings["workspace_paths"],
            exclude_folders=self.settings.get("exclude_folders", [])
        )
        workspace_duration = perf_counter() - workspace_start

        self.write_log(f"Workspace scan: {workspace_duration:.3f} sec")
        self.write_log(f"Repositories found: {len(self.repositories)}")

        ui_start = perf_counter()
        self.repo_table.setRowCount(len(self.repositories))
        ui_prepare_duration = perf_counter() - ui_start
        self.write_log(f"UI table prepare: {ui_prepare_duration:.3f} sec")

        slowest_repo_name = ""
        slowest_repo_duration = 0.0

        for row, repo in enumerate(self.repositories):
            repo_start = perf_counter()

            metadata_start = perf_counter()
            metadata = load_project_metadata(repo)
            metadata_duration = perf_counter() - metadata_start

            branch_start = perf_counter()
            branch = get_branch(repo)
            branch_duration = perf_counter() - branch_start

            state_start = perf_counter()
            sync_state = detect_sync_state(repo, branch)
            state_duration = perf_counter() - state_start

            local_start = perf_counter()
            local_date = get_local_last_commit_date(repo)
            local_duration = perf_counter() - local_start

            remote_start = perf_counter()
            remote_date = get_remote_last_commit_date(repo, branch)
            remote_duration = perf_counter() - remote_start

            row_ui_start = perf_counter()
            self.repo_table.setItem(row, 0, QTableWidgetItem(metadata.name))
            self.repo_table.setItem(row, 1, QTableWidgetItem(branch))
            self.repo_table.setItem(row, 2, QTableWidgetItem(translate_sync_state(sync_state)))
            self.repo_table.setItem(row, 3, QTableWidgetItem(local_date))
            self.repo_table.setItem(row, 4, QTableWidgetItem(remote_date))
            self.repo_table.setItem(row, 5, QTableWidgetItem(metadata.version))
            self.repo_table.setItem(row, 6, QTableWidgetItem(metadata.status))
            self.repo_table.setItem(row, 7, QTableWidgetItem(metadata.description))
            self.repo_table.setItem(row, 8, QTableWidgetItem(str(repo)))
            row_ui_duration = perf_counter() - row_ui_start

            repo_duration = perf_counter() - repo_start

            if repo_duration > slowest_repo_duration:
                slowest_repo_duration = repo_duration
                slowest_repo_name = repo.name

            self.write_log(
                f"Repo: {repo.name} | total={repo_duration:.3f}s | "
                f"metadata={metadata_duration:.3f}s | "
                f"branch={branch_duration:.3f}s | "
                f"state={state_duration:.3f}s | "
                f"local={local_duration:.3f}s | "
                f"remote={remote_duration:.3f}s | "
                f"ui={row_ui_duration:.3f}s"
            )

        total_duration = perf_counter() - total_start

        self.write_log("-" * 70)
        self.write_log(f"Slowest repository: {slowest_repo_name or 'n/a'} ({slowest_repo_duration:.3f} sec)")
        self.write_log(f"TOTAL scan time: {total_duration:.3f} sec")
        self.write_log("=" * 70)

        self.statusBar().showMessage(
            f"Найдено репозиториев: {len(self.repositories)} | Сканирование: {total_duration:.2f} сек"
        )

    def on_repository_selected(self):
        selected_items = self.repo_table.selectedItems()
        if not selected_items:
            return

        selected_row = selected_items[0].row()
        path_item = self.repo_table.item(selected_row, 8)
        if not path_item:
            return

        self.selected_repo = Path(path_item.text())
        metadata = load_project_metadata(self.selected_repo)

        project_text = [
            f"Проект: {metadata.name}",
            f"Код: {metadata.code}",
            f"Версия: {metadata.version}",
            f"Статус: {metadata.status}",
            f"Приоритет: {metadata.priority}",
            f"Тип: {metadata.project_type}",
            f"Источник данных: {metadata.source}",
            "",
            "Описание:",
            metadata.description,
            "",
            "Путь:",
            str(self.selected_repo),
            "",
            "Доступные действия:",
            "- Проверить изменения",
            "- Получить изменения",
            "- Отправить изменения",
            "- Открыть DevAdvisor",
            "- Открыть в VS Code",
            "- Открыть на GitHub"
        ]

        self.project_info.setText("\n".join(project_text))
        self.statusBar().showMessage(f"Выбран проект: {metadata.name}")

    def open_devadvisor(self):
        if not self.selected_repo:
            QMessageBox.warning(self, "DevHub", "Сначала выберите проект.")
            return

        if self.devadvisor_window is None:
            self.devadvisor_window = DevAdvisorWindow(self.selected_repo, self)
        else:
            self.devadvisor_window.set_project(self.selected_repo)

        self.devadvisor_window.show()
        self.devadvisor_window.raise_()
        self.devadvisor_window.activateWindow()
        self.statusBar().showMessage("DevAdvisor открыт")

    def run_selected_git_command(self, command: list[str]):
        if not self.selected_repo:
            QMessageBox.warning(self, "DevHub", "Сначала выберите проект.")
            return

        if self.current_git_task and self.current_git_task.isRunning():
            QMessageBox.information(
                self,
                "DevHub",
                "Другая Git-операция уже выполняется. Дождитесь завершения."
            )
            return

        command_name = "git " + " ".join(command)

        self.write_log("")
        self.write_log("=" * 70)
        self.write_log(f"Команда для выбранного проекта: {command_name}")
        self.write_log("=" * 70)

        self.statusBar().showMessage(f"Выполняется: {command_name}...")

        self.fetch_button.setEnabled(False)
        self.pull_button.setEnabled(False)
        self.push_button.setEnabled(False)
        self.sync_button.setEnabled(False)
        self.scan_button.setEnabled(False)

        self.current_git_task = GitTask(self.selected_repo, command, self)
        self.current_git_task.progress.connect(self.write_log)
        self.current_git_task.finished_success.connect(self.on_git_task_finished)
        self.current_git_task.finished_error.connect(self.on_git_task_error)
        self.current_git_task.finished.connect(self.on_git_task_cleanup)
        self.current_git_task.start()

    def on_git_task_finished(self, result):
        for line in format_result(result):
            self.write_log(line)

        self.statusBar().showMessage(f"Команда выполнена: {result.status}")

        # Важно: scan_repositories пока остается синхронным.
        # Его вынесем в фон в следующем пакете стабилизации.
        self.scan_repositories()

    def on_git_task_error(self, error_text: str):
        self.write_log("")
        self.write_log("ERROR")
        self.write_log(error_text)
        self.statusBar().showMessage("Ошибка выполнения Git-команды")
        QMessageBox.critical(self, "Ошибка Git", error_text)

    def on_git_task_cleanup(self):
        self.fetch_button.setEnabled(True)
        self.pull_button.setEnabled(True)
        self.push_button.setEnabled(True)
        self.sync_button.setEnabled(True)
        self.scan_button.setEnabled(True)
        self.current_git_task = None

    def sync_all(self):
        self.log_output.clear()
        self.statusBar().showMessage("Синхронизация запущена...")

        allowed_branches = self.settings.get(
            "allowed_branches",
            [self.settings.get("default_branch", "main")]
        )

        results, summary = sync_all_repositories(
            workspace_paths=self.settings["workspace_paths"],
            allowed_branches=allowed_branches,
            exclude_folders=self.settings.get("exclude_folders", [])
        )

        for result in results:
            for line in format_result(result):
                self.write_log(line)

        for line in format_summary(summary):
            self.write_log(line)

        self.statusBar().showMessage(
            f"Готово: успешно {summary.success}, пропущено {summary.skipped}, ошибок {summary.errors}"
        )
        self.scan_repositories()
