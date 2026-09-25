from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem


class RepositoryListWidget(QTableWidget):
    """Таблица локальных Git-репозиториев."""

    repository_selected = Signal(Path)

    COLUMNS = (
        "Проект",
        "Ветка",
        "Состояние",
        "Локально",
        "GitHub",
        "Версия",
        "Статус",
        "Описание",
        "Путь",
    )

    def __init__(self) -> None:
        super().__init__(0, len(self.COLUMNS))
        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.itemSelectionChanged.connect(self._emit_selection)

    def set_repositories(self, rows: list[dict[str, str]]) -> None:
        self.clearContents()
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = (
                row["name"],
                row["branch"],
                row["sync_state"],
                row["local_date"],
                row["remote_date"],
                row["version"],
                row["status"],
                row["description"],
                row["path"],
            )
            for column_index, value in enumerate(values):
                self.setItem(row_index, column_index, QTableWidgetItem(value))

    def _emit_selection(self) -> None:
        selected = self.selectedItems()
        if not selected:
            return
        path_item = self.item(selected[0].row(), 8)
        if path_item is not None:
            self.repository_selected.emit(Path(path_item.text()))
