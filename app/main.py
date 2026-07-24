import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from app.engineering_intelligence_window import EngineeringIntelligenceWindow
from app.research_evolution_window import ResearchEvolutionWindow
from app.services.application_lifecycle import ApplicationLifecycleManager
from app.shutdown_dialog import ShutdownDialog
from app.ui import MainWindow


class DevHubMainWindow(MainWindow):
    """Main window controlled by the central application lifecycle manager."""

    def __init__(self) -> None:
        super().__init__()
        self._allow_close = False
        self.engineering_intelligence_window: EngineeringIntelligenceWindow | None = None
        self.lifecycle = ApplicationLifecycleManager(self)
        self._install_exit_button()
        self._activate_stars_entry()
        self.lifecycle.startup()

    def _install_exit_button(self) -> None:
        self.exit_button = QPushButton("ВЫХОД")
        self.exit_button.setObjectName("ExitButton")
        self.exit_button.setToolTip(
            "Безопасно завершает DevHub, сохраняет сессию и останавливает фоновые задачи."
        )
        self.exit_button.setMinimumWidth(110)
        self.exit_button.clicked.connect(self.request_exit)
        self.statusBar().addPermanentWidget(self.exit_button)

        self.setStyleSheet(
            self.styleSheet()
            + """
            QPushButton#ExitButton {
                font-weight: bold;
                padding: 7px 18px;
                border: 1px solid #8f1d1d;
                border-radius: 4px;
                background-color: #b3261e;
                color: white;
            }
            QPushButton#ExitButton:hover { background-color: #8f1d1d; }
            QPushButton#ExitButton:pressed { background-color: #6f1515; }
            """
        )

    def _activate_stars_entry(self) -> None:
        self.runtime_label.setCursor(Qt.PointingHandCursor)
        self.runtime_label.setToolTip(
            "Нажмите, чтобы открыть Engineering Intelligence и Technology Hub."
        )
        self.runtime_label.mousePressEvent = self._on_runtime_label_clicked

        intelligence_menu = self.menuBar().addMenu("Intelligence")
        action = QAction("⭐ Engineering Intelligence", self)
        action.setToolTip("Открывает Technology Hub и инженерную базу знаний DevHub.")
        action.triggered.connect(self.open_engineering_intelligence)
        intelligence_menu.addAction(action)

    def _on_runtime_label_clicked(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.open_engineering_intelligence(open_technology_hub=True)

    def open_engineering_intelligence(self, open_technology_hub: bool = False) -> None:
        if not self.lifecycle.can_start_task():
            return

        stars_count = self.status_service.data.github_stars
        if self.engineering_intelligence_window is None:
            self.engineering_intelligence_window = EngineeringIntelligenceWindow(
                stars_count=stars_count,
                parent=self,
            )
        else:
            self.engineering_intelligence_window.update_stars_count(stars_count)

        if open_technology_hub:
            self.engineering_intelligence_window.open_technology_hub()

        self.engineering_intelligence_window.show()
        self.engineering_intelligence_window.raise_()
        self.engineering_intelligence_window.activateWindow()
        self.statusBar().showMessage("Engineering Intelligence открыт")

    def request_exit(self) -> None:
        if self.lifecycle.shutdown_started:
            return

        answer = QMessageBox.question(
            self,
            "Выход из DevHub",
            "Завершить работу DevHub?\n\n"
            "Рабочее пространство будет сохранено, фоновые операции — остановлены, "
            "ресурсы приложения — освобождены.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.exit_button.setEnabled(False)
        dialog = ShutdownDialog(self)
        dialog.show()
        QApplication.processEvents()

        self.lifecycle.shutdown(dialog.set_step)
        self._allow_close = True

        # Keep the completed state visible briefly without blocking shutdown work.
        QTimer.singleShot(350, lambda: self._finish_exit(dialog))

    def _finish_exit(self, dialog: ShutdownDialog) -> None:
        dialog.close()
        self.close()
        self.lifecycle.quit_application()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close:
            event.accept()
            return

        event.ignore()
        self.request_exit()


def install_research_evolution_center(window: DevHubMainWindow) -> None:
    window.research_evolution_window = None

    def open_center() -> None:
        if not window.lifecycle.can_start_task():
            return
        if window.research_evolution_window is None:
            window.research_evolution_window = ResearchEvolutionWindow()
        window.research_evolution_window.show()
        window.research_evolution_window.raise_()
        window.research_evolution_window.activateWindow()

    menu = window.menuBar().addMenu("Исследования")
    action = QAction("Центр исследований и эволюции", window)
    action.setToolTip(
        "Открывает единый реестр идей, исследований, GitHub Stars и производных проектов."
    )
    action.triggered.connect(open_center)
    menu.addAction(action)


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    window = DevHubMainWindow()
    install_research_evolution_center(window)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
