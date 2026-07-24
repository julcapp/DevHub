from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout


class ShutdownDialog(QDialog):
    """Small modal dialog showing the real shutdown sequence."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Завершение работы DevHub")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setFixedSize(440, 180)

        self.title_label = QLabel("Завершение работы DevHub")
        self.title_label.setObjectName("ShutdownTitle")
        self.step_label = QLabel("Подготовка безопасного завершения...")
        self.step_label.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.footer = QLabel("DevHub Engineering Platform")
        self.footer.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.step_label)
        layout.addWidget(self.progress)
        layout.addStretch()
        layout.addWidget(self.footer)

        self.setStyleSheet(
            """
            QDialog { background: #f5f5f5; }
            QLabel#ShutdownTitle { font-size: 17px; font-weight: bold; }
            QProgressBar { height: 22px; text-align: center; }
            """
        )

    def set_step(self, text: str, progress: int) -> None:
        self.step_label.setText(f"✓ {text}")
        self.progress.setValue(progress)
