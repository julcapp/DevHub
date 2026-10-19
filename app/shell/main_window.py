from __future__ import annotations

from collections.abc import Callable
from html import escape
from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QFrame,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.platform import PlatformKernel
from app.workspaces.architecture import ArchitectureWorkspace
from app.workspaces.explorer import ProjectExplorerWorkspace
from app.workspaces.git import GitWorkspace
from app.workspaces.notebook import EngineeringNotebookWorkspace


class PlaceholderWorkspace(QWidget):
    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("WorkspaceTitle")
        text = QLabel(description)
        text.setWordWrap(True)
        text.setObjectName("WorkspaceDescription")
        layout.addWidget(heading)
        layout.addWidget(text)
        layout.addStretch()


class DashboardWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        heading = QLabel("Обзор платформы")
        heading.setObjectName("WorkspaceTitle")
        summary = QLabel(
            "DevHub Shell запущен. На первом этапе оболочка отделяет навигацию, "
            "рабочие пространства, инспектор и системный журнал от прикладных модулей."
        )
        summary.setWordWrap(True)
        summary.setObjectName("WorkspaceDescription")
        layout.addWidget(heading)
        layout.addWidget(summary)
        layout.addStretch()


class DevHubShell(QMainWindow):
    """Платформенная оболочка DevHub."""

    def __init__(self, kernel: PlatformKernel) -> None:
        super().__init__()
        self.kernel = kernel
        self.setWindowTitle("DevHub v0.6 Alpha — Engineering Operating System")
        self.resize(1500, 900)
        self.navigation = QListWidget()
        self.workspace_host = QStackedWidget()
        self.inspector = QTextEdit()
        self._inspector_visible = True
        self.bottom_panel = QTextEdit()
        self._workspace_factories: dict[str, Callable[[], QWidget]] = {}
        self._workspace_indexes: dict[str, int] = {}
        self._build_ui()
        self._register_workspaces()
        self._bind_events()
        self.navigation.setCurrentRow(0)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        title_bar = QFrame()
        title_bar.setObjectName("TitleBar")
        title_layout = QHBoxLayout(title_bar)
        title = QLabel("DevHub")
        title.setObjectName("ProductTitle")
        subtitle = QLabel("Инженерная операционная система")
        subtitle.setObjectName("ProductSubtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_bar.setStyleSheet("QFrame#TitleBar { background-color: #1f2937; } QLabel#ProductTitle { background: transparent; color: #ffffff; } QLabel#ProductSubtitle { background: transparent; color: #cbd5e1; } QLabel#KernelState { background: transparent; color: #86efac; }")
        title_layout.addStretch()
        kernel_state = QLabel("● Ядро: готово")
        kernel_state.setObjectName("KernelState")
        title_layout.addWidget(kernel_state)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.navigation.setObjectName("Navigation")
        self.navigation.setMinimumWidth(175)
        self.navigation.setMaximumWidth(320)
        self.navigation.currentItemChanged.connect(self._activate_workspace)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(12, 12, 12, 8)
        center_layout.addWidget(self.workspace_host, 1)
        self.bottom_panel.setObjectName("BottomPanel")
        self.bottom_panel.setReadOnly(True)
        self.bottom_panel.setFixedHeight(150)
        self.bottom_panel.setPlaceholderText("История событий платформы")
        center_layout.addWidget(self.bottom_panel)

        inspector_frame = QFrame()
        self.inspector_frame = inspector_frame
        inspector_frame.setObjectName("InspectorFrame")
        inspector_frame.setMinimumWidth(215)
        inspector_frame.setMaximumWidth(430)
        inspector_layout = QVBoxLayout(inspector_frame)
        inspector_title = QLabel("Инспектор")
        inspector_title.setObjectName("PanelTitle")
        self.inspector.setReadOnly(True)
        self.inspector.setText(
            "Здесь будут отображаться свойства выбранного инженерного актива, "
            "его статус, связи, история и рекомендации DevAdvisor."
        )
        inspector_layout.addWidget(inspector_title)
        inspector_layout.addWidget(self.inspector)

        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setChildrenCollapsible(False)
        for widget in (self.navigation, center, inspector_frame):
            self.content_splitter.addWidget(widget)
        self.content_splitter.setStretchFactor(1, 1)
        self.content_splitter.setSizes([220, 980, 270])
        self.inspector_toggle = QPushButton("Скрыть инспектор")
        self.inspector_toggle.setToolTip("Освободить место для рабочего пространства")
        self.inspector_toggle.clicked.connect(self._toggle_inspector)
        title_layout.addWidget(self.inspector_toggle)
        root_layout.addWidget(title_bar)
        root_layout.addWidget(self.content_splitter, 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("DevHub готов к работе")
        self._apply_style()

    def _register_workspaces(self) -> None:
        entries = [
            ("Обзор", lambda: DashboardWorkspace()),
            ("Проекты", self._create_projects_workspace),
            ("Проводник", lambda: ProjectExplorerWorkspace()),
            ("Знания", lambda: PlaceholderWorkspace("Знания", "Инженерные активы, связи и корпоративная память.")),
            ("Звёздочки", self._create_stars_workspace),
            ("Идеи", lambda: EngineeringNotebookWorkspace()),
            ("Исследования", lambda: PlaceholderWorkspace("Исследования", "Гипотезы, эксперименты, выводы и доказательства.")),
            ("Архитектура", lambda: ArchitectureWorkspace()),
            ("Документация", lambda: PlaceholderWorkspace("Документация", "Структурированные документы как инженерные активы.")),
            ("Разработка", lambda: GitWorkspace()),
            ("AI", lambda: PlaceholderWorkspace("AI", "Engineering Intelligence Layer и специализированные агенты.")),
            ("Аналитика", lambda: PlaceholderWorkspace("Аналитика", "Состояние проектов, риски, зрелость и динамика.")),
            ("Инновации", lambda: PlaceholderWorkspace("Инновации", "Портфель идей, исследований и новых продуктов.")),
            ("Центр ИС", lambda: PlaceholderWorkspace("Центр интеллектуальной собственности", "Патенты, ноу-хау и защищаемые активы.")),
            ("Автоматизация", lambda: PlaceholderWorkspace("Автоматизация", "Сценарии, правила и инженерные процессы.")),
            ("Настройки", lambda: PlaceholderWorkspace("Настройки", "Конфигурация платформы, модулей и рабочих пространств.")),
        ]
        for title, factory in entries:
            self._workspace_factories[title] = factory
            self.navigation.addItem(QListWidgetItem(title))

    @staticmethod
    def _create_projects_workspace() -> QWidget:
        from app.workspaces.projects_workspace import ProjectsWorkspace
        return ProjectsWorkspace()

    @staticmethod
    def _create_stars_workspace() -> QWidget:
        from app.workspaces.stars import StarsWorkspace

        return StarsWorkspace()

    def _activate_workspace(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        if current is None:
            return
        title = current.text()
        if title not in self._workspace_indexes:
            widget = self._workspace_factories[title]()
            self._workspace_indexes[title] = self.workspace_host.addWidget(widget)
            if title == "Проекты":
                widget.project_selected.connect(self._show_project_in_inspector)
        self.workspace_host.setCurrentIndex(self._workspace_indexes[title])
        if title != "Проекты":
            self.inspector.setPlainText("Выберите объект для просмотра его свойств.")
        self.statusBar().showMessage(f"Открыто рабочее пространство: {title}")
        self.kernel.events.publish("workspace.activated", {"workspace": title})

    def _show_project_in_inspector(self, repo: object) -> None:
        if not isinstance(repo, dict):
            self.inspector.setPlainText("Выберите проект в списке.")
            return
        name = escape(str(repo.get("full_name") or "Без названия"))
        description = escape(str(repo.get("description") or "Описание не указано"))
        language = escape(str(repo.get("language") or "Не указан"))
        updated = escape(str(repo.get("updated_at") or "Неизвестно")[:10])
        stars = int(repo.get("stargazers_count") or 0)
        kind = "Форк" if repo.get("fork") else "Собственный репозиторий"
        self.inspector.setHtml(
            f"<h3>{name}</h3><p>{description}</p><hr>"
            f"<p><b>Тип:</b> {kind}</p><p><b>Язык:</b> {language}</p>"
            f"<p><b>Звёзд:</b> {stars}</p><p><b>Обновлён:</b> {updated}</p>"
        )

    def _toggle_inspector(self) -> None:
        self._inspector_visible = not self._inspector_visible
        self.inspector_frame.setVisible(self._inspector_visible)
        self.inspector_toggle.setText("Скрыть инспектор" if self._inspector_visible else "Показать инспектор")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.width() < 1100 and self._inspector_visible:
            self._toggle_inspector()

    def _bind_events(self) -> None:
        self.kernel.events.subscribe("platform.started", self._write_event)
        self.kernel.events.subscribe("platform.stopping", self._write_event)
        self.kernel.events.subscribe("workspace.activated", self._write_event)

    def _write_event(self, event: dict[str, object]) -> None:
        self.bottom_panel.append(
            f"[{event.get('timestamp', '')}] {event.get('event', 'event')} — "
            f"{event.get('workspace', event.get('state', ''))}"
        )

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.kernel.stop()
        super().closeEvent(event)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f4f6f8; color: #20242a; }
            QFrame#TitleBar { background: #1f2937; min-height: 58px; }
            QLabel#ProductTitle { color: white; font-size: 21px; font-weight: 700; }
            QLabel#ProductSubtitle { color: #cbd5e1; font-size: 13px; }
            QLabel#KernelState { color: #86efac; font-weight: 600; }
            QListWidget#Navigation { background: #111827; color: #d1d5db; border: 0; padding: 8px; font-size: 14px; }
            QListWidget#Navigation::item { padding: 10px 12px; border-radius: 5px; }
            QListWidget#Navigation::item:selected { background: #2563eb; color: white; font-weight: 700; border-left: 4px solid #93c5fd; }
            QListWidget#Navigation::item:hover:!selected { background: #263447; color: white; }
            QSplitter::handle { background: #dbe3ec; width: 5px; }
            QSplitter::handle:hover { background: #93c5fd; }
            QLabel#WorkspaceTitle { font-size: 24px; font-weight: 700; }
            QLabel#WorkspaceDescription { font-size: 14px; color: #4b5563; padding-top: 8px; }
            QLabel#ArchitectureMetric { font-size: 18px; font-weight: 700; }
            QFrame#InspectorFrame { background: #ffffff; border-left: 1px solid #d1d5db; }
            QLabel#PanelTitle { font-size: 15px; font-weight: 700; }
            QTextEdit, QPlainTextEdit, QTreeView, QListWidget, QLineEdit { background: white; border: 1px solid #d1d5db; border-radius: 4px; padding: 8px; }
            QTextEdit#BottomPanel { font-family: Consolas; font-size: 11px; }
            QStatusBar { background: #e5e7eb; }
            """
        )
