from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QListWidget,
    QLabel
)

from app.config import load_settings
from app.git_manager import (
    find_repositories,
    sync_all_repositories,
    format_result,
    format_summary
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DevHub v0.1 Alpha")
        self.resize(1000, 700)

        self.settings = load_settings()
        self.repositories = []

        self.title = QLabel("DevHub v0.1 Alpha — центр управления разработкой")

        self.repo_list = QListWidget()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        self.scan_button = QPushButton("Найти репозитории")
        self.sync_button = QPushButton("Синхронизировать все")

        self.scan_button.clicked.connect(self.scan_repositories)
        self.sync_button.clicked.connect(self.sync_all)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.scan_button)
        button_layout.addWidget(self.sync_button)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("Репозитории:"))
        layout.addWidget(self.repo_list)
        layout.addWidget(QLabel("Журнал:"))
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def write_log(self, text: str):
        self.log_output.append(text)

    def scan_repositories(self):
        self.repo_list.clear()
        self.log_output.clear()

        self.repositories = find_repositories(
            workspace_paths=self.settings["workspace_paths"],
            exclude_folders=self.settings.get("exclude_folders", [])
        )

        for repo in self.repositories:
            self.repo_list.addItem(repo.name)

        self.write_log(f"Найдено репозиториев: {len(self.repositories)}")

    def sync_all(self):
        self.log_output.clear()

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