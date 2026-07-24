from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


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
    """First-stage shell for DevHub Engineering Intelligence."""

    def __init__(self, stars_count: int = 0, parent=None) -> None:
        super().__init__(parent)
        self.stars_count = stars_count
        self.setWindowTitle("DevHub — Engineering Intelligence")
        self.resize(1180, 760)
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
            cards.addWidget(self._metric_card("Technologies", "0", "🧩"))
            cards.addWidget(self._metric_card("AI Analyses", "0", "🧠"))
            cards.addWidget(self._metric_card("Evolution Tasks", "0", "🚀"))
            layout.addLayout(cards)
        elif title == "Technology Hub":
            text = QLabel(
                f"Подключено GitHub Stars: {self.stars_count}\n\n"
                "Следующий этап: синхронизация starred-репозиториев, импорт README, License, Releases "
                "и формирование карточек технологий."
            )
            text.setWordWrap(True)
            text.setObjectName("PageBody")
            layout.addWidget(text)
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

    def _metric_card(self, title: str, value: str, icon: str) -> QFrame:
        card = QFrame()
        card.setObjectName("MetricCard")
        card_layout = QVBoxLayout(card)

        icon_label = QLabel(icon)
        icon_label.setObjectName("MetricIcon")
        value_label = QLabel(value)
        value_label.setObjectName("MetricValue")
        title_label = QLabel(title)
        title_label.setObjectName("MetricTitle")

        card_layout.addWidget(icon_label)
        card_layout.addWidget(value_label)
        card_layout.addWidget(title_label)
        return card

    def update_stars_count(self, stars_count: int) -> None:
        self.stars_count = stars_count
        current_row = self.navigation.currentRow()
        self.pages.removeWidget(self.pages.widget(0))
        self.pages.insertWidget(0, self._create_page("Dashboard"))
        self.pages.removeWidget(self.pages.widget(1))
        self.pages.insertWidget(1, self._create_page("Technology Hub"))
        self.navigation.setCurrentRow(current_row if current_row >= 0 else 0)

    def open_technology_hub(self) -> None:
        self.navigation.setCurrentRow(1)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f5f7fa; }
            QListWidget#IntelligenceNavigation {
                background: #1f2937;
                color: #f9fafb;
                border: none;
                padding: 14px 8px;
                font-size: 14px;
            }
            QListWidget#IntelligenceNavigation::item {
                padding: 12px 14px;
                margin: 2px 0;
                border-radius: 6px;
            }
            QListWidget#IntelligenceNavigation::item:selected {
                background: #374151;
                color: white;
            }
            QLabel#PageHeading { font-size: 26px; font-weight: 700; color: #111827; }
            QLabel#PageSubtitle { font-size: 14px; color: #4b5563; }
            QLabel#PageBody { font-size: 14px; color: #374151; }
            QFrame#MetricCard {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                min-width: 175px;
                padding: 12px;
            }
            QLabel#MetricIcon { font-size: 24px; }
            QLabel#MetricValue { font-size: 26px; font-weight: 700; color: #111827; }
            QLabel#MetricTitle { font-size: 13px; color: #6b7280; }
            """
        )
