from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QGridLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QSplitter, QTextEdit, QVBoxLayout, QWidget

from app.workspaces.architecture.controller import ArchitectureSummary, ArchitectureWorkspaceController
from app.workspaces.architecture.graph_view import ArchitectureGraphView


class ArchitectureWorkspace(QWidget):
    """Центр архитектуры: сводка, интерактивная карта, модули и предупреждения."""

    def __init__(self) -> None:
        super().__init__()
        self.controller = ArchitectureWorkspaceController()
        self.root_path: Path | None = None
        self.summary: ArchitectureSummary | None = None
        self.project_label = QLabel("Проект не выбран")
        self.status_label = QLabel("Выберите локальный проект и запустите анализ.")
        self.dependencies = QListWidget(); self.warnings = QListWidget(); self.modules = QListWidget()
        self.module_details = QTextEdit(); self.module_details.setReadOnly(True)
        self.graph_view = ArchitectureGraphView()
        self.metrics: dict[str, QLabel] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout(); title = QLabel("Центр архитектуры"); title.setObjectName("WorkspaceTitle")
        choose_button = QPushButton("Выбрать проект"); choose_button.clicked.connect(self.choose_project)
        analyze_button = QPushButton("Анализировать"); analyze_button.clicked.connect(self.analyze)
        header.addWidget(title); header.addStretch(); header.addWidget(choose_button); header.addWidget(analyze_button)
        layout.addLayout(header); layout.addWidget(self.project_label); layout.addWidget(self.status_label)

        grid = QGridLayout()
        names = [("files","Файлы"),("folders","Папки"),("modules","Модули"),("classes","Классы"),("methods","Методы"),("functions","Функции"),("imports","Импорты"),("internal_dependencies","Внутренние зависимости"),("nodes_total","Узлы графа"),("edges_total","Связи графа")]
        for index, (key, text) in enumerate(names):
            value = QLabel("—"); value.setObjectName("ArchitectureMetric"); self.metrics[key] = value
            row, column = index // 2, (index % 2) * 2; grid.addWidget(QLabel(text), row, column); grid.addWidget(value, row, column + 1)
        layout.addLayout(grid)
        layout.addWidget(QLabel("Карта модулей")); layout.addWidget(self.graph_view, 2)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget(); left_layout = QVBoxLayout(left); left_layout.setContentsMargins(0,0,0,0); left_layout.addWidget(QLabel("Модули проекта")); left_layout.addWidget(self.modules)
        right = QWidget(); right_layout = QVBoxLayout(right); right_layout.setContentsMargins(0,0,0,0); right_layout.addWidget(QLabel("Карточка модуля")); right_layout.addWidget(self.module_details)
        splitter.addWidget(left); splitter.addWidget(right); splitter.setStretchFactor(1,1); layout.addWidget(splitter,2)

        bottom = QSplitter(Qt.Orientation.Horizontal)
        dep_box = QWidget(); dep_layout = QVBoxLayout(dep_box); dep_layout.setContentsMargins(0,0,0,0); dep_layout.addWidget(QLabel("Все зависимости модулей")); dep_layout.addWidget(self.dependencies)
        warn_box = QWidget(); warn_layout = QVBoxLayout(warn_box); warn_layout.setContentsMargins(0,0,0,0); warn_layout.addWidget(QLabel("Архитектурные предупреждения")); warn_layout.addWidget(self.warnings)
        bottom.addWidget(dep_box); bottom.addWidget(warn_box); layout.addWidget(bottom,1)
        self.modules.currentRowChanged.connect(self._show_module)
        self.graph_view.module_selected.connect(self._select_module_by_name)

    def choose_project(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if directory:
            self.root_path = Path(directory); self.project_label.setText(str(self.root_path)); self.status_label.setText("Проект выбран. Нажмите «Анализировать».")

    def analyze(self) -> None:
        if self.root_path is None:
            self.status_label.setText("Сначала выберите проект."); return
        self.status_label.setText("Индексирование и анализ проекта...")
        try: self.summary = self.controller.analyze(self.root_path)
        except (FileNotFoundError, OSError, ValueError) as error:
            self.status_label.setText(f"Ошибка анализа: {error}"); return
        self._show_summary(self.summary)

    def _show_summary(self, summary: ArchitectureSummary) -> None:
        self.project_label.setText(f"{summary.project_name} — {summary.project_path}")
        for key, label in self.metrics.items(): label.setText(str(getattr(summary,key)))
        self.dependencies.clear(); self.modules.clear(); self.module_details.clear(); self.warnings.clear()
        self.dependencies.addItems(summary.dependencies or ("Внутренние зависимости пока не обнаружены",))
        self.modules.addItems([item.name for item in summary.module_details])
        self.warnings.addItems(summary.warnings or ("Критических архитектурных предупреждений не обнаружено",))
        self.graph_view.show_summary(summary)
        if summary.module_details: self.modules.setCurrentRow(0)
        cycle_text = f", циклов: {len(summary.cycles)}" if summary.cycles else ""
        self.status_label.setText(f"Анализ завершён: {summary.nodes_total} узлов, {summary.edges_total} связей{cycle_text}.")

    def _select_module_by_name(self, name: str) -> None:
        matches = self.modules.findItems(name, Qt.MatchFlag.MatchExactly)
        if matches: self.modules.setCurrentItem(matches[0])

    def _show_module(self, row: int) -> None:
        if self.summary is None or row < 0 or row >= len(self.summary.module_details): self.module_details.clear(); return
        item = self.summary.module_details[row]
        depends = "\n".join(f"  → {name}" for name in item.dependencies) or "  —"; used_by = "\n".join(f"  ← {name}" for name in item.dependents) or "  —"; symbols = "\n".join(f"  {name}" for name in item.symbols) or "  —"
        self.module_details.setPlainText(f"Модуль: {item.name}\nФайл: {item.path}\n\nЗависит от:\n{depends}\n\nИспользуется в:\n{used_by}\n\nСимволы:\n{symbols}")
