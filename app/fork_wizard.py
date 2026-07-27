from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.providers.github_provider import StarredRepository


@dataclass(slots=True)
class ForkPlan:
    source_repository: str
    target_owner: str
    target_name: str
    local_path: str
    evolution_branch: str
    visibility: str
    register_internal_project: bool
    create_standard_docs: bool


class ForkWizard(QDialog):
    """Collects and validates a safe development-fork plan without executing it yet."""

    def __init__(self, technology: StarredRepository, github_user: str = "", parent=None) -> None:
        super().__init__(parent)
        self.technology = technology
        self.setWindowTitle("DevHub — Create Development Fork")
        self.resize(720, 650)
        self._build_ui(github_user)
        self._update_preview()

    def _build_ui(self, github_user: str) -> None:
        root = QVBoxLayout(self)
        heading = QLabel("Создание собственного проекта из технологии")
        heading.setStyleSheet("font-size: 20px; font-weight: 700;")
        root.addWidget(heading)
        root.addWidget(QLabel(f"Источник: {self.technology.full_name}"))

        form = QFormLayout()
        self.owner_edit = QLineEdit(github_user)
        self.name_edit = QLineEdit(self.technology.name)
        self.branch_edit = QLineEdit(
            f"devhub/evolution-{self.technology.name.lower().replace('_', '-')}"
        )
        self.visibility_combo = QComboBox()
        self.visibility_combo.addItems(["Сохранить видимость Fork", "Public", "Private"])

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(str(Path.home() / "Documents" / "GitHub" / self.technology.name))
        browse = QPushButton("Выбрать...")
        browse.clicked.connect(self._choose_path)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse)

        form.addRow("Владелец Fork:", self.owner_edit)
        form.addRow("Имя нового репозитория:", self.name_edit)
        form.addRow("Ветка развития:", self.branch_edit)
        form.addRow("Видимость:", self.visibility_combo)
        form.addRow("Локальная папка:", path_row)
        root.addLayout(form)

        self.license_check = QCheckBox(
            f"Лицензия проверена: {self.technology.license_name or 'не указана'}"
        )
        self.internal_project_check = QCheckBox("Зарегистрировать в Internal Projects")
        self.internal_project_check.setChecked(True)
        self.docs_check = QCheckBox(
            "Создать PROJECT.yaml, ROADMAP.md, ADR, CHANGELOG.md и AI_NOTES.md"
        )
        self.docs_check.setChecked(True)
        root.addWidget(self.license_check)
        root.addWidget(self.internal_project_check)
        root.addWidget(self.docs_check)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        root.addWidget(QLabel("План выполнения"))
        root.addWidget(self.preview, 1)

        for widget in (
            self.owner_edit,
            self.name_edit,
            self.branch_edit,
            self.path_edit,
        ):
            widget.textChanged.connect(self._update_preview)
        self.visibility_combo.currentTextChanged.connect(self._update_preview)
        self.internal_project_check.toggled.connect(self._update_preview)
        self.docs_check.toggled.connect(self._update_preview)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText("Сохранить план")
        buttons.accepted.connect(self._accept_plan)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _choose_path(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Выберите рабочую папку")
        if selected:
            self.path_edit.setText(str(Path(selected) / self.name_edit.text().strip()))

    def plan(self) -> ForkPlan:
        return ForkPlan(
            source_repository=self.technology.full_name,
            target_owner=self.owner_edit.text().strip(),
            target_name=self.name_edit.text().strip(),
            local_path=self.path_edit.text().strip(),
            evolution_branch=self.branch_edit.text().strip(),
            visibility=self.visibility_combo.currentText(),
            register_internal_project=self.internal_project_check.isChecked(),
            create_standard_docs=self.docs_check.isChecked(),
        )

    def _update_preview(self) -> None:
        plan = self.plan()
        target = f"{plan.target_owner or '<владелец>'}/{plan.target_name or '<имя>'}"
        steps = [
            f"1. Проверить лицензию источника {plan.source_repository}.",
            f"2. Создать Fork: {target}.",
            f"3. Клонировать в: {plan.local_path or '<папка>'}.",
            f"4. Настроить origin → {target}.",
            f"5. Настроить upstream → {plan.source_repository}.",
            f"6. Создать ветку: {plan.evolution_branch or '<ветка>'}.",
        ]
        if plan.create_standard_docs:
            steps.append("7. Создать стандартный комплект инженерной документации DevHub.")
        if plan.register_internal_project:
            steps.append("8. Зарегистрировать проект и происхождение в Internal Projects.")
        steps.append("9. Выполнение начнётся только после отдельного финального подтверждения.")
        self.preview.setPlainText("\n".join(steps))

    def _accept_plan(self) -> None:
        plan = self.plan()
        if not plan.target_owner or not plan.target_name or not plan.evolution_branch:
            QMessageBox.warning(self, "Fork Wizard", "Заполните владельца, имя и ветку развития.")
            return
        if not plan.local_path:
            QMessageBox.warning(self, "Fork Wizard", "Укажите локальную рабочую папку.")
            return
        if not self.license_check.isChecked():
            QMessageBox.warning(
                self,
                "Fork Wizard",
                "Перед сохранением плана подтвердите проверку лицензии.",
            )
            return
        self.accept()
