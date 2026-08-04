from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class GitToolbarWidget(QWidget):
    """Панель основных Git-операций выбранного репозитория."""

    fetch_requested = Signal()
    pull_requested = Signal()
    push_requested = Signal()
    commit_requested = Signal()
    history_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.fetch_button = QPushButton("Fetch")
        self.pull_button = QPushButton("Pull")
        self.push_button = QPushButton("Push")
        self.commit_button = QPushButton("Commit")
        self.history_button = QPushButton("История")

        self.fetch_button.clicked.connect(self.fetch_requested)
        self.pull_button.clicked.connect(self.pull_requested)
        self.push_button.clicked.connect(self.push_requested)
        self.commit_button.clicked.connect(self.commit_requested)
        self.history_button.clicked.connect(self.history_requested)

        for button in self.buttons:
            layout.addWidget(button)
        layout.addStretch()
        self.setEnabled(False)

    @property
    def buttons(self) -> tuple[QPushButton, ...]:
        return (
            self.fetch_button,
            self.pull_button,
            self.push_button,
            self.commit_button,
            self.history_button,
        )

    def set_busy(self, busy: bool) -> None:
        for button in self.buttons:
            button.setEnabled(not busy)
