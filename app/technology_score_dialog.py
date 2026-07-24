from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
)

from app.models.technology_profile import TechnologyProfile


class TechnologyScoreDialog(QDialog):
    """Editor for internal DevHub assessment and knowledge fields."""

    SCORE_FIELDS = (
        ("stability", "Стабильность", 20),
        ("activity", "Активность разработки", 15),
        ("documentation", "Документация", 10),
        ("security", "Безопасность", 15),
        ("compatibility", "Совместимость", 20),
        ("internal_experience", "Внутренний опыт", 20),
    )

    def __init__(self, profile: TechnologyProfile, parent=None) -> None:
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("DevHub — инженерная оценка технологии")
        self.resize(640, 720)
        self.inputs: dict[str, QSpinBox] = {}
        self._build_ui()
        self._refresh_total()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        intro = QLabel(
            "Оцените технологию по шкале 0–100. Итоговый DevHub Score рассчитывается "
            "по утверждённым весам и отделён от популярности GitHub."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        for field_name, title, weight in self.SCORE_FIELDS:
            control = QSpinBox()
            control.setRange(0, 100)
            control.setSuffix(" / 100")
            control.setValue(getattr(self.profile.score, field_name))
            control.valueChanged.connect(self._refresh_total)
            self.inputs[field_name] = control
            form.addRow(f"{title} ({weight}%)", control)
        layout.addLayout(form)

        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(self.total_label)

        layout.addWidget(QLabel("Internet Intelligence — краткое резюме"))
        self.internet_summary = QPlainTextEdit(self.profile.internet_summary)
        self.internet_summary.setPlaceholderText(
            "Проверенные внешние сведения, тенденции, статьи и контекст. Источники указываются отдельно."
        )
        layout.addWidget(self.internet_summary)

        layout.addWidget(QLabel("Источники — по одному URL в строке"))
        self.source_urls = QPlainTextEdit("\n".join(self.profile.source_urls))
        self.source_urls.setMaximumHeight(110)
        layout.addWidget(self.source_urls)

        layout.addWidget(QLabel("Внутренние заметки и опыт DevHub"))
        self.internal_notes = QPlainTextEdit(self.profile.internal_notes)
        self.internal_notes.setPlaceholderText(
            "Где применяли, какие проблемы возникли, принятые решения и рекомендации."
        )
        layout.addWidget(self.internal_notes)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _calculated_total(self) -> float:
        weights = {
            "stability": 0.20,
            "activity": 0.15,
            "documentation": 0.10,
            "security": 0.15,
            "compatibility": 0.20,
            "internal_experience": 0.20,
        }
        return round(sum(self.inputs[name].value() * weight for name, weight in weights.items()) / 10, 1)

    def _refresh_total(self) -> None:
        if hasattr(self, "total_label"):
            self.total_label.setText(f"DevHub Technology Score: {self._calculated_total()} / 10")

    def _save_and_accept(self) -> None:
        for field_name, control in self.inputs.items():
            setattr(self.profile.score, field_name, control.value())
        self.profile.internet_summary = self.internet_summary.toPlainText().strip()
        self.profile.source_urls = [
            line.strip() for line in self.source_urls.toPlainText().splitlines() if line.strip()
        ]
        self.profile.internal_notes = self.internal_notes.toPlainText().strip()
        self.accept()
