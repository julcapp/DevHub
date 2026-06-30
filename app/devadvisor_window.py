from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.devadvisor import build_project_advice
from app.project_metadata import load_project_metadata


class DevAdvisorWindow(QMainWindow):
    """Отдельное рабочее пространство DevAdvisor."""

    def __init__(self, repo_path: Path | None = None, parent=None):
        super().__init__(parent)

        self.repo_path = repo_path

        self.setWindowTitle("DevAdvisor — инженерный консультант проекта")
        self.resize(980, 720)

        self.init_ui()
        self.refresh()

    def init_ui(self):
        central_widget = QWidget()
        root_layout = QHBoxLayout()

        self.nav_list = QListWidget()
        self.nav_list.addItems(
            [
                "Сегодня",
                "Инженерный обзор",
                "Документация",
                "Архитектура",
                "DevScore",
                "Риски",
                "История",
                "Рекомендации",
            ]
        )
        self.nav_list.setFixedWidth(210)
        self.nav_list.setCurrentRow(1)
        self.nav_list.setToolTip(
            "Разделы DevAdvisor. Сейчас активен базовый инженерный обзор проекта."
        )

        content_layout = QVBoxLayout()

        self.title_label = QLabel("DevAdvisor")
        self.title_label.setObjectName("AdvisorTitle")

        self.subtitle_label = QLabel(
            "Инженерный консультант DevHub: анализирует проект и предлагает действия."
        )

        self.review_output = QTextEdit()
        self.review_output.setReadOnly(True)
        self.review_output.setToolTip(
            "Здесь отображается инженерный обзор выбранного проекта: README, DHMS, документация и рекомендации."
        )

        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Обновить анализ")
        self.refresh_button.setToolTip(
            "Повторно анализирует выбранный проект и обновляет рекомендации DevAdvisor."
        )
        self.refresh_button.clicked.connect(self.refresh)

        self.close_button = QPushButton("Закрыть")
        self.close_button.setToolTip("Закрывает окно DevAdvisor.")
        self.close_button.clicked.connect(self.close)

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.close_button)

        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.subtitle_label)
        content_layout.addWidget(self.review_output)
        content_layout.addLayout(button_layout)

        root_layout.addWidget(self.nav_list)
        root_layout.addLayout(content_layout)

        central_widget.setLayout(root_layout)
        self.setCentralWidget(central_widget)

        self.apply_style()

    def apply_style(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f5f5;
            }

            QLabel#AdvisorTitle {
                font-size: 20px;
                font-weight: bold;
                padding: 6px;
            }

            QLabel {
                font-weight: bold;
            }

            QListWidget {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
                font-size: 13px;
                padding: 4px;
            }

            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
                font-family: Consolas, Arial;
                font-size: 12px;
            }

            QPushButton {
                padding: 8px;
                font-size: 13px;
            }
            """
        )

    def set_project(self, repo_path: Path):
        self.repo_path = repo_path
        self.refresh()

    def refresh(self):
        if self.repo_path is None:
            self.review_output.setText(
                "DevAdvisor\n\n"
                "Проект не выбран.\n\n"
                "Вернитесь в главное окно DevHub, выберите проект и нажмите "
                "«Открыть DevAdvisor»."
            )
            return

        metadata = load_project_metadata(self.repo_path)
        advice = build_project_advice(self.repo_path)

        header = [
            "DevAdvisor",
            "",
            f"Проект: {metadata.name}",
            f"Код: {metadata.code}",
            f"Версия: {metadata.version}",
            f"Статус: {metadata.status}",
            f"Источник данных: {metadata.source}",
            "",
            "Инженерный обзор",
            "-" * 60,
        ]

        footer = [
            "",
            "-" * 60,
            "Формат рекомендации DevAdvisor:",
            "1. Что обнаружено.",
            "2. Почему это важно.",
            "3. Что рекомендуется сделать.",
        ]

        self.review_output.setText("\n".join(header + advice + footer))
