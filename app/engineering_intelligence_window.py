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

from app.fork_wizard import ForkWizard
from app.models.technology_profile import TechnologyProfile, TechnologyStatus
from app.providers.github_provider import StarredRepository
from app.services.technology_profile_service import TechnologyProfileService
from app.technology_score_dialog import TechnologyScoreDialog


SECTIONS = [
    ("🏠", "Dashboard"), ("⭐", "Technology Hub"), ("📚", "Knowledge Base"),
    ("🧠", "AI Advisor"), ("🔬", "Research Lab"), ("🚀", "Evolution"),
    ("🏗", "Architecture"), ("📦", "Components"), ("📖", "Documentation"),
    ("📊", "Analytics"), ("⚙", "Integrations"), ("🗂", "Internal Projects"),
]


class EngineeringIntelligenceWindow(QMainWindow):
    """Engineering knowledge workspace and technology lifecycle manager."""

    def __init__(self, stars_count: int = 0, technologies=None, parent=None) -> None:
        super().__init__(parent)
        self.stars_count = stars_count
        self.technologies: list[StarredRepository] = technologies or []
        self.filtered_technologies: list[StarredRepository] = []
        self.selected_technology: StarredRepository | None = None
        self.profile_service = TechnologyProfileService()
        self.profiles = self.profile_service.load_all()
        self.setWindowTitle("DevHub — Engineering Intelligence")
        self.resize(1320, 850)
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
            cards.addWidget(self._metric_card("Internal Profiles", str(len(self.profiles)), "📘"))
            assessed = sum(1 for profile in self.profiles.values() if profile.score.total() > 0)
            cards.addWidget(self._metric_card("Assessed", str(assessed), "📊"))
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
            "Библиотека технологий: исследование, оценка, внешний контекст, Fork и собственная ветка развития."
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
        self.status_filter = QComboBox()
        self.status_filter.addItem("Все статусы")
        self.status_filter.addItems([status.value for status in TechnologyStatus])
        self.technology_search.textChanged.connect(self._rebuild_technology_list)
        self.technology_language.currentTextChanged.connect(self._rebuild_technology_list)
        self.status_filter.currentTextChanged.connect(self._rebuild_technology_list)
        filters.addWidget(self.technology_search, 1)
        filters.addWidget(self.technology_language)
        filters.addWidget(self.status_filter)
        layout.addLayout(filters)

        splitter = QSplitter(Qt.Horizontal)
        self.technology_list = QListWidget()
        self.technology_list.setObjectName("TechnologyList")
        self.technology_list.currentRowChanged.connect(self._show_technology)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        self.technology_title = QLabel("Выберите технологию")
        self.technology_title.setObjectName("TechnologyTitle")
        self.technology_meta = QLabel("После синхронизации здесь появится паспорт технологии.")
        self.technology_meta.setObjectName("PageSubtitle")
        self.technology_meta.setWordWrap(True)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Внутренний статус DevHub"))
        self.profile_status = QComboBox()
        self.profile_status.addItems([status.value for status in TechnologyStatus])
        self.profile_status.currentTextChanged.connect(self._save_selected_status)
        status_row.addWidget(self.profile_status)
        status_row.addStretch()

        self.technology_description = QTextEdit()
        self.technology_description.setReadOnly(True)

        actions = QHBoxLayout()
        self.open_github_button = QPushButton("Открыть GitHub")
        self.assess_button = QPushButton("Оценка и знания")
        self.fork_button = QPushButton("Create Development Fork")
        self.open_github_button.clicked.connect(self._open_selected_on_github)
        self.assess_button.clicked.connect(self._open_assessment_editor)
        self.fork_button.clicked.connect(self._open_fork_wizard)
        for button in (self.open_github_button, self.assess_button, self.fork_button):
            button.setEnabled(False)
            actions.addWidget(button)
        actions.addStretch()

        detail_layout.addWidget(self.technology_title)
        detail_layout.addWidget(self.technology_meta)
        detail_layout.addLayout(status_row)
        detail_layout.addWidget(self.technology_description, 1)
        detail_layout.addLayout(actions)

        splitter.addWidget(self.technology_list)
        splitter.addWidget(detail)
        splitter.setSizes([410, 750])
        layout.addWidget(splitter, 1)
        self._refresh_language_filter()
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
        self.technology_language.setCurrentIndex(max(self.technology_language.findText(selected), 0))
        self.technology_language.blockSignals(False)

    def _profile_for(self, technology: StarredRepository) -> TechnologyProfile:
        return self.profile_service.get_or_create(self.profiles, technology.full_name)

    def _rebuild_technology_list(self) -> None:
        if not hasattr(self, "technology_list"):
            return
        query = self.technology_search.text().strip().lower()
        language = self.technology_language.currentText()
        status = self.status_filter.currentText()
        current_name = self.selected_technology.full_name if self.selected_technology else ""
        self.filtered_technologies = []
        self.technology_list.clear()

        for technology in self.technologies:
            profile = self._profile_for(technology)
            searchable = " ".join(
                [technology.full_name, technology.description, technology.language, " ".join(technology.topics)]
            ).lower()
            if query and query not in searchable:
                continue
            if language != "Все языки" and technology.language != language:
                continue
            if status != "Все статусы" and profile.status.value != status:
                continue
            self.filtered_technologies.append(technology)
            score_text = f"Score {profile.score.total()}" if profile.score.total() else "Не оценена"
            item = QListWidgetItem(
                f"⭐ {technology.full_name}\n{profile.status.value} · {score_text} · "
                f"{technology.language or 'Язык n/a'} · ★ {technology.stars}"
            )
            item.setToolTip(technology.description or technology.full_name)
            self.technology_list.addItem(item)

        if self.filtered_technologies:
            selected_row = next(
                (i for i, item in enumerate(self.filtered_technologies) if item.full_name == current_name), 0
            )
            self.technology_list.setCurrentRow(selected_row)
        else:
            self.selected_technology = None
            self.technology_title.setText("Технологии не найдены")
            self.technology_meta.setText("Обновите GitHub-статистику или измените фильтры.")
            self.technology_description.clear()
            for button in (self.open_github_button, self.assess_button, self.fork_button):
                button.setEnabled(False)

    def _show_technology(self, row: int) -> None:
        if row < 0 or row >= len(self.filtered_technologies):
            return
        technology = self.filtered_technologies[row]
        profile = self._profile_for(technology)
        self.selected_technology = technology
        self.technology_title.setText(technology.full_name)
        self.technology_meta.setText(
            f"Язык: {technology.language or 'не указан'} | Лицензия: {technology.license_name or 'не указана'} | "
            f"Stars: {technology.stars} | Forks: {technology.forks} | Issues: {technology.open_issues}\n"
            f"Основная ветка: {technology.default_branch} | Обновлено: {technology.updated_at or 'n/a'}"
        )
        self.profile_status.blockSignals(True)
        self.profile_status.setCurrentText(profile.status.value)
        self.profile_status.blockSignals(False)

        topics = ", ".join(technology.topics) if technology.topics else "не указаны"
        internet = profile.internet_summary or (
            "Внешняя информация ещё не собрана. Факты из Интернета должны сопровождаться источниками."
        )
        sources = "\n".join(f"• {url}" for url in profile.source_urls) or "• Источники не добавлены"
        internal = profile.internal_notes or "Внутренний опыт пока не зафиксирован."
        score = profile.score.total()
        score_details = (
            f"Стабильность {profile.score.stability}/100 · Активность {profile.score.activity}/100 · "
            f"Документация {profile.score.documentation}/100\n"
            f"Безопасность {profile.score.security}/100 · Совместимость {profile.score.compatibility}/100 · "
            f"Наш опыт {profile.score.internal_experience}/100"
        )
        self.technology_description.setPlainText(
            f"ОФИЦИАЛЬНЫЕ ДАННЫЕ\n{technology.description or 'Описание отсутствует.'}\n\n"
            f"Topics: {topics}\nClone URL: {technology.clone_url}\n\n"
            f"INTERNET INTELLIGENCE\n{internet}\n\nИСТОЧНИКИ\n{sources}\n\n"
            f"DEVHUB EXPERIENCE\n{internal}\n\n"
            f"DEVHUB TECHNOLOGY SCORE\n{score} / 10\n{score_details}\n\n"
            f"EVOLUTION\nFork: {profile.fork_repository or 'не создан'}\n"
            f"Upstream: {profile.upstream_repository or technology.full_name}\n"
            f"Ветка развития: {profile.evolution_branch or 'не создана'}"
        )
        self.open_github_button.setEnabled(bool(technology.html_url))
        self.assess_button.setEnabled(True)
        self.fork_button.setEnabled(bool(technology.full_name))

    def _save_selected_status(self, value: str) -> None:
        if self.selected_technology is None:
            return
        profile = self._profile_for(self.selected_technology)
        profile.status = TechnologyStatus(value)
        self.profile_service.save_all(self.profiles)
        self._rebuild_technology_list()

    def _open_assessment_editor(self) -> None:
        technology = self.selected_technology
        if technology is None:
            return
        profile = self._profile_for(technology)
        dialog = TechnologyScoreDialog(profile, self)
        if dialog.exec() != TechnologyScoreDialog.Accepted:
            return
        self.profile_service.save_all(self.profiles)
        self._rebuild_technology_list()
        QMessageBox.information(
            self,
            "Technology Hub",
            "Инженерная оценка, внешние источники и внутренние заметки сохранены.",
        )

    def _open_selected_on_github(self) -> None:
        if self.selected_technology and self.selected_technology.html_url:
            QDesktopServices.openUrl(QUrl(self.selected_technology.html_url))

    def _open_fork_wizard(self) -> None:
        technology = self.selected_technology
        if technology is None:
            return
        parent = self.parent()
        github_user = str(getattr(parent, "settings", {}).get("github_user", "")) if parent else ""
        wizard = ForkWizard(technology, github_user=github_user, parent=self)
        if wizard.exec() != ForkWizard.Accepted:
            return
        plan = wizard.plan()
        profile = self._profile_for(technology)
        profile.status = TechnologyStatus.PLANNED
        profile.fork_repository = f"{plan.target_owner}/{plan.target_name}"
        profile.upstream_repository = technology.full_name
        profile.evolution_branch = plan.evolution_branch
        self.profile_service.save_all(self.profiles)
        self._rebuild_technology_list()
        QMessageBox.information(
            self,
            "Fork Wizard",
            "План сохранён в карточке технологии. Репозиторий ещё не создан. "
            "Исполнение будет добавлено после подключения безопасной GitHub-авторизации.",
        )

    def open_technology_hub(self) -> None:
        self.navigation.setCurrentRow(1)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f5f7fa; }
            QListWidget#IntelligenceNavigation { background: #1f2937; color: #f9fafb; border: none; padding: 14px 8px; font-size: 14px; }
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
        """)
