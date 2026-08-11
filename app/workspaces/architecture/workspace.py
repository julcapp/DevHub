from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.workspaces.architecture.controller import ArchitectureSummary, ArchitectureWorkspaceController


class ArchitectureWorkspace(QWidget):
    """Первая рабочая версия Центра архитектуры DevHub."""

    def __init__(self) -> None:
        super().__init__()
        self.controller = ArchitectureWorkspaceController()
        self.root_path: Path | None = None
        self.project_label = QLabel("Проект не выбран")
        self.status_label = QLabel("Выберите локальный проект и запустите анализ.")
        self.dependencies = QListWidget()
        self.metrics: dict[str, QLabel] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Центр архитектуры")
        title.setObjectName("WorkspaceTitle")
        choose_button = QPushButton("Выбрать проект")
        choose_button.clicked.connect(self.choose_project)
        analyze_button = QPushButton("Анализировать")
        analyze_button.clicked.connect(self.analyze)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(choose_button)
        header.addWidget(analyze_button)

        layout.addLayout(header)
        layout.addWidget(self.project_label)
        layout.addWidget(self.status_label)

        metrics_grid = QGridLayout()
        metric_names = [
            ("files", "Файлы"),
            ("folders", "Папки"),
            ("modules", "Модули"),
            ("classes", "Классы"),
            ("methods", "Методы"),
            ("functions", "Функции"),
            ("imports", "Импорты"),
            ("internal_dependencies", "Внутренние зависимости"),
            ("nodes_total", "Узлы графа"),
            ("edges_total", "Связи графа"),
        ]
        for index, (key, label_text) in enumerate(metric_names):
            label = QLabel(label_text)
            value = QLabel("—")
            value.setObjectName("ArchitectureMetric")
            self.metrics[key] = value
            row = index // 2
            column = (index % 2) * 2
            metrics_grid.addWidget(label, row, column)
            metrics_grid.addWidget(value, row, column + 1)

        layout.addLayout(metrics_grid)
        layout.addWidget(QLabel("Зависимости модулей"))
        self.dependencies.setAlternatingRowColors(True)
        layout.addWidget(self.dependencies, 1)

    def choose_project(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if not directory:
            return
        self.root_path = Path(directory)
        self.project_label.setText(str(self.root_path))
        self.status_label.setText("Проект выбран. Нажмите «Анализировать».")

    def analyze(self) -> None:
        if self.root_path is None:
            self.status_label.setText("Сначала выберите проект.")
            return
        self.status_label.setText("Индексирование и анализ проекта...")
        try:
            summary = self.controller.analyze(self.root_path)
        except (FileNotFoundError, OSError, ValueError) as error:
            self.status_label.setText(f"Ошибка анализа: {error}")
            return
        self._show_summary(summary)

    def _show_summary(self, summary: ArchitectureSummary) -> None:
        self.project_label.setText(f"{summary.project_name} — {summary.project_path}")
        for key in self.metrics:
            self.metrics[key].setText(str(getattr(summary, key)))
        self.dependencies.clear()
        if summary.dependencies:
            self.dependencies.addItems(summary.dependencies)
        else:
            self.dependencies.addItem("Внутренние зависимости пока не обнаружены")
        self.status_label.setText(
            f"Анализ завершён: {summary.nodes_total} узлов, {summary.edges_total} связей."
        )
