from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import EngineeringObjectType
from app.db.session import create_session_factory
from app.services.engineering_object_service import EngineeringObjectService


TYPE_LABELS = {
    EngineeringObjectType.PROJECT: "Проект",
    EngineeringObjectType.REPOSITORY: "Репозиторий",
    EngineeringObjectType.STAR: "GitHub Star",
    EngineeringObjectType.IDEA: "Идея",
    EngineeringObjectType.RESEARCH: "Исследование",
    EngineeringObjectType.TECHNOLOGY: "Технология",
    EngineeringObjectType.ARTIFACT: "Артефакт",
    EngineeringObjectType.EVOLUTION: "Эволюция",
    EngineeringObjectType.ADR: "ADR",
    EngineeringObjectType.DOCUMENT: "Документ",
}


class ResearchEvolutionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DevHub — Центр исследований и эволюции")
        self.resize(1100, 720)
        self.session_factory = create_session_factory()
        self._build_ui()
        self.refresh_objects()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Центр исследований и эволюции"))
        root.addWidget(
            QLabel(
                "Единый реестр идей, исследований, GitHub Stars, технологий и производных проектов."
            )
        )

        actions = QHBoxLayout()
        self.refresh_button = QPushButton("Обновить")
        self.create_button = QPushButton("Создать объект")
        actions.addWidget(self.refresh_button)
        actions.addWidget(self.create_button)
        actions.addStretch()
        root.addLayout(actions)

        self.status_label = QLabel("Подключение к Core DB…")
        root.addWidget(self.status_label)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["EO-ID", "Тип", "Название", "Статус", "Создан"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnWidth(0, 170)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 420)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 180)
        root.addWidget(self.table)

        self.refresh_button.clicked.connect(self.refresh_objects)
        self.create_button.clicked.connect(self.open_create_dialog)

    def refresh_objects(self) -> None:
        try:
            with self.session_factory() as session:
                items = EngineeringObjectService(session).list_objects()
                self.table.setRowCount(len(items))
                for row, item in enumerate(items):
                    self.table.setItem(row, 0, QTableWidgetItem(item.eo_id))
                    self.table.setItem(
                        row,
                        1,
                        QTableWidgetItem(TYPE_LABELS.get(item.object_type, item.object_type.value)),
                    )
                    self.table.setItem(row, 2, QTableWidgetItem(item.title))
                    self.table.setItem(row, 3, QTableWidgetItem(item.status.value))
                    created = item.created_at.astimezone().strftime("%d.%m.%Y %H:%M")
                    self.table.setItem(row, 4, QTableWidgetItem(created))
            self.status_label.setText(f"Core DB подключена. Объектов: {len(items)}")
            self.create_button.setEnabled(True)
        except SQLAlchemyError as exc:
            self.table.setRowCount(0)
            self.create_button.setEnabled(False)
            self.status_label.setText(
                "Core DB недоступна. Выполните Alembic-миграцию и проверьте DEVHUB_DATABASE_URL."
            )
            self.status_label.setToolTip(str(exc))

    def open_create_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Новый инженерный объект")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        type_box = QComboBox()
        for object_type, label in TYPE_LABELS.items():
            type_box.addItem(label, object_type)
        title_input = QLineEdit()
        description_input = QTextEdit()
        description_input.setMaximumHeight(120)

        form.addRow("Тип", type_box)
        form.addRow("Название", title_input)
        form.addRow("Описание", description_input)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        save_button = QPushButton("Создать")
        cancel_button = QPushButton("Отмена")
        buttons.addStretch()
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

        cancel_button.clicked.connect(dialog.reject)

        def save() -> None:
            try:
                with self.session_factory.begin() as session:
                    item = EngineeringObjectService(session).create_object(
                        object_type=type_box.currentData(),
                        title=title_input.text(),
                        description=description_input.toPlainText(),
                    )
                QMessageBox.information(
                    self,
                    "Объект создан",
                    f"Создан инженерный объект {item.eo_id}",
                )
                dialog.accept()
                self.refresh_objects()
            except (ValueError, SQLAlchemyError) as exc:
                QMessageBox.critical(self, "Ошибка создания", str(exc))

        save_button.clicked.connect(save)
        dialog.exec()
