from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.providers.github_provider import StarredRepository


SECTIONS = [
    ("🏠", "Dashboard"),
    ("⭐", "Technology Hub"),
    ("📚", "Knowledge Base"),
    ("🧠", "AI Advisor"),
    ("🔬", "Research Lab"),
    ("🚀", "Evolution"),
    ("🏗", "Architecture"),
    ("📦", "Components"),
    ("📖", "Documentation"),
    ("📊", "Analytics"),
    ("⚙", "Integrations"),
    ("🗂", "Internal Projects"),
]


class EngineeringIntelligenceWindow(QMainWindow):
    """Engineering knowledge workspace with a usable Technology Hub."""

    def __init__(
        self,
        stars_count: int = 0,
        technologies: list[StarredRepository] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.stars_count = stars_count
        self.technologies = technologies or []
        self.filtered_technologies: list[StarredRepository] = []
        self.selected_technology: StarredRepository | None = None
        self.setWindowTitle("DevHub — Engineering Intelligence")
        self.resize(1240, 800)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.navigation = QListWidget()
        self.navigation.setObjectName("IntelligenceNavigation")
        self.navigation.setFixedWidth(245)
        for icon, title in SECTIONS:
            QListWidgetItem(f"{icon}  {title}", self.navigation)

        self.pages = QStackedWidget()
        for _, title in SECTIONS:
            self.pages.addWidget(self._create_page(title))

        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        layout.addWidget(self.navigation)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)
        self._apply_style()

    def _create_page(self, title: str) -> QWidget:
        if title == "Technology Hub":
            return self._create_technology_hub_page()

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        heading = QLabel(title)
        heading.setObjectName("PageHeading")
        layout.addWidget(heading)

        if title == "Dashboard":
            subtitle = QLabel(
                "Единый центр инженерных знаний, технологий, архитектуры и развития проектов DevHub."
            )
            subtitle.setObjectName("PageSubtitle")
            subtitle.setWordWrap(True)
            layout.addWidget(subtitle)
            cards = QHBoxLayout()
            cards.addWidget(self._metric_card("GitHub Stars", str(self.stars_count), "⭐"))
            cards.addWidget(self._metric_card("Technologies", str(len(self.technologies)), "🧩"))
            cards.addWidget(self._metric_card("AI Analyses", "0", "🧠"))
            cards.addWidget(self._metric_card("Evolution Tasks", "0", "🚀"))
            layout.addLayout(cards)
        else:
            text = QLabel(
                "Раздел подготовлен в архитектуре Engineering Intelligence. "
                "Данные и рабочие инструменты будут подключаться поэтапно."
            )
            text.setWordWrap(True)
            text.setObjectName("PageBody")
            layout.addWidget(text)

        layout.addStretch()
        return page

    def _create_technology_hub_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        heading = QLabel("Technology Hub")
        heading.setObjectName("PageHeading")
        subtitle = QLabel(
            "Библиотека starred-репозиториев GitHub: изучение, классификация, форк и создание собственной ветки развития."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        filters = QHBoxLayout()
        self.technology_search = QLineEdit()
        self.technology_search.setPlaceholderText("Поиск по названию, владельцу, описанию или теме...")
        self.technology_language = QComboBox()
        self.technology_language.addItem("Все языки")
        self.technology_search.textChanged.connect(self._filter_technologies)
        self.technology_language.currentTextChanged.connect(self._filter_technologies)
        filters.addWidget(self.technology_search, 1)
        filters.addWidget(self.technology_language)
        layout.addLayout(filters)

        splitter = QSplitter(Qt.Horizontal)
        self.technology_list = QListWidget()
        self.technology_list.setObjectName("TechnologyList")
        self.technology_list.currentRowChanged.connect(self._show_technology)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        self.technology_title = QLabel("Выберите технологию")
        self.technology_title.setObjectName("TechnologyTitle")
        self.technology_meta = QLabel("После синхронизации здесь появится паспорт starred-репозитория.")
        self.technology_meta.setObjectName("PageSubtitle")
        self.technology_meta.setWordWrap(True)
        self.technology_description = QTextEdit()
        self.technology_description.setReadOnly(True)
        self.technology_description.setPlaceholderText("Описание технологии")

        actions = QHBoxLayout()
        self.open_github_button = QPushButton("Открыть GitHub")
        self.fork_button = QPushButton("Fork → собственный проект")
        self.open_github_button.clicked.connect(self._open_selected_on_github)
        self.fork_button.clicked.connect(self._show_fork_plan)
        self.open_github_button.setEnabled(False)
        self.fork_button.setEnabled(False)
        actions.addWidget(self.open_github_button)
        actions.addWidget(self.fork_button)
        actions.addStretch()

        detail_layout.addWidget(self.technology_title)
        detail_layout.addWidget(self.technology_meta)
        detail_layout.addWidget(self.technology_description, 1)
        detail_layout.addLayout(actions)

        splitter.addWidget(self.technology_list)
        splitter.addWidget(detail)
        splitter.setSizes([390, 700])
        layout.addWidget(splitter, 1)
        self._rebuild_technology_list()
        return page

    def _metric_card(self, title: str, value: str, icon: str) -> QFrame:
        card = QFrame()
        card.setObjectName("MetricCard")
        card_layout = QVBoxLayout(card)
        for text, object_name in ((icon, "MetricIcon"), (value, "MetricValue"), (title, "MetricTitle")):
            label = QLabel(text)
            label.setObjectName(object_name)
            card_layout.addWidget(label)
        return card

    def update_data(self, stars_count: int, technologies: list[StarredRepository]) -> None:
        self.stars_count = stars_count
        self.technologies = technologies
        self._refresh_language_filter()
        self._rebuild_technology_list()
        current_row = self.navigation.currentRow()
        old_dashboard = self.pages.widget(0)
        self.pages.removeWidget(old_dashboard)
        old_dashboard.deleteLater()
        self.pages.insertWidget(0, self._create_page("Dashboard"))
        self.navigation.setCurrentRow(current_row if current_row >= 0 else 0)

    def update_stars_count(self, stars_count: int) -> None:
        self.update_data(stars_count, self.technologies)

    def _refresh_language_filter(self) -> None:
        if not hasattr(self, "technology_language"):
            return
        selected = self.technology_language.currentText()
        languages = sorted({item.language for item in self.technologies if item.language})
        self.technology_language.blockSignals(True)
        self.technology_language.clear()
        self.technology_language.addItem("Все языки")
        self.technology_language.addItems(languages)
        index = self.technology_language.findText(selected)
        self.technology_language.setCurrentIndex(max(index, 0))
        self.technology_language.blockSignals(False)

    def _filter_technologies(self) -> None:
        self._rebuild_technology_list()

    def _rebuild_technology_list(self) -> None:
        if not hasattr(self, "technology_list"):
            return
        query = self.technology_search.text().strip().lower() if hasattr(self, "technology_search") else ""
        language = self.technology_language.currentText() if hasattr(self, "technology_language") else "Все языки"
        self.filtered_technologies = []
        self.technology_list.clear()

        for technology in self.technologies:
            searchable = " ".join(
                [technology.full_name, technology.description, technology.language, " ".join(technology.topics)]
            ).lower()
            if query and query not in searchable:
                continue
            if language != "Все языки" and technology.language != language:
                continue
            self.filtered_technologies.append(technology)
            item = QListWidgetItem(
                f"⭐ {technology.full_name}\n"
                f"{technology.language or 'Язык не указан'} · {technology.license_name or 'License n/a'} · "
                f"★ {technology.stars}"
            )
            item.setToolTip(technology.description or technology.full_name)
            self.technology_list.addItem(item)

        if self.filtered_technologies:
            self.technology_list.setCurrentRow(0)
        else:
            self.selected_technology = None
            self.technology_title.setText("Технологии не найдены")
            self.technology_meta.setText(
                "Обновите GitHub-статистику или измените параметры поиска."
            )
            self.technology_description.clear()
            self.open_github_button.setEnabled(False)
            self.fork_button.setEnabled(False)

    def _show_technology(self, row: int) -> None:
        if row < 0 or row >= len(self.filtered_technologies):
            return
        technology = self.filtered_technologies[row]
        self.selected_technology = technology
        self.technology_title.setText(technology.full_name)
        self.technology_meta.setText(
            f"Язык: {technology.language or 'не указан'}   |   "
            f"Лицензия: {technology.license_name or 'не указана'}   |   "
            f"Stars: {technology.stars}   |   Forks: {technology.forks}   |   "
            f"Issues: {technology.open_issues}\n"
            f"Основная ветка: {technology.default_branch}   |   Обновлено: {technology.updated_at or 'n/a'}"
        )
        topics = ", ".join(technology.topics) if technology.topics else "не указаны"
        self.technology_description.setPlainText(
            f"Описание\n{technology.description or 'Описание отсутствует.'}\n\n"
            f"Topics\n{topics}\n\n"
            "Статус DevHub\n🟡 Изучается\n\n"
            "Дальнейшие возможности\n"
            "• импорт README, Releases и документации;\n"
            "• AI-анализ применимости;\n"
            "• связь с внутренними проектами;\n"
            "• создание управляемого форка и собственной ветки развития."
        )
        self.open_github_button.setEnabled(bool(technology.html_url))
        self.fork_button.setEnabled(bool(technology.full_name))

    def _open_selected_on_github(self) -> None:
        if self.selected_technology and self.selected_technology.html_url:
            QDesktopServices.openUrl(QUrl(self.selected_technology.html_url))

    def _show_fork_plan(self) -> None:
        technology = self.selected_technology
        if technology is None:
            return
        proposed_branch = f"devhub/evolution-{technology.name.lower().replace('_', '-')}"
        QMessageBox.information(
            self,
            "Fork и собственная ветка развития",
            f"Источник: {technology.full_name}\n"
            f"Основная ветка источника: {technology.default_branch}\n"
            f"Предлагаемая ветка развития: {proposed_branch}\n\n"
            "Безопасный сценарий DevHub:\n"
            "1. Проверить лицензию и ограничения использования.\n"
            "2. Создать Fork в вашем GitHub-аккаунте.\n"
            "3. Клонировать Fork в отдельную рабочую папку.\n"
            "4. Добавить исходный репозиторий как remote upstream.\n"
            "5. Создать отдельную ветку развития.\n"
            "6. Зарегистрировать проект в Internal Projects.\n"
            "7. Сохранить происхождение, лицензию и историю синхронизации.\n\n"
            "На следующем этапе добавим мастер выполнения с GitHub-токеном, выбором имени, "
            "папки и ветки. До подтверждения пользователя DevHub ничего не создаёт.",
        )

    def open_technology_hub(self) -> None:
        self.navigation.setCurrentRow(1)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f5f7fa; }
            QListWidget#IntelligenceNavigation {
                background: #1f2937; color: #f9fafb; border: none;
                padding: 14px 8px; font-size: 14px;
            }
            QListWidget#IntelligenceNavigation::item { padding: 12px 14px; margin: 2px 0; border-radius: 6px; }
            QListWidget#IntelligenceNavigation::item:selected { background: #374151; color: white; }
            QListWidget#TechnologyList { background: white; border: 1px solid #d1d5db; font-size: 13px; }
            QListWidget#TechnologyList::item { padding: 10px; border-bottom: 1px solid #e5e7eb; }
            QListWidget#TechnologyList::item:selected { background: #dbeafe; color: #111827; }
            QLabel#PageHeading { font-size: 26px; font-weight: 700; color: #111827; }
            QLabel#TechnologyTitle { font-size: 22px; font-weight: 700; color: #111827; }
            QLabel#PageSubtitle { font-size: 14px; color: #4b5563; }
            QLabel#PageBody { font-size: 14px; color: #374151; }
            QFrame#MetricCard { background: white; border: 1px solid #d1d5db; border-radius: 10px; min-width: 175px; padding: 12px; }
            QLabel#MetricIcon { font-size: 24px; }
            QLabel#MetricValue { font-size: 26px; font-weight: 700; color: #111827; }
            QLabel#MetricTitle { font-size: 13px; color: #6b7280; }
            QLineEdit, QComboBox, QTextEdit { background: white; border: 1px solid #cbd5e1; border-radius: 5px; padding: 7px; }
            QPushButton { padding: 8px 14px; }
            """
        )
