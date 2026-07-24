import sys

from PySide6.QtCore import QThread
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from app.research_evolution_window import ResearchEvolutionWindow
from app.ui import MainWindow


class DevHubMainWindow(MainWindow):
    """Main window with one controlled shutdown path for every exit action."""

    def __init__(self) -> None:
        super().__init__()
        self._shutdown_in_progress = False
        self._install_exit_button()

    def _install_exit_button(self) -> None:
        self.exit_button = QPushButton("ВЫХОД")
        self.exit_button.setObjectName("ExitButton")
        self.exit_button.setToolTip(
            "Корректно завершает DevHub, закрывает дочерние окна и останавливает фоновые задачи."
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
            QPushButton#ExitButton:hover {
                background-color: #8f1d1d;
            }
            QPushButton#ExitButton:pressed {
                background-color: #6f1515;
            }
            """
        )

    def request_exit(self) -> None:
        answer = QMessageBox.question(
            self,
            "Выход из DevHub",
            "Завершить работу DevHub?\n\n"
            "Открытые окна будут закрыты, фоновые операции — остановлены, "
            "ресурсы приложения — освобождены.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.close()

    def _stop_task(self, task: QThread | None, task_name: str) -> None:
        if task is None or not task.isRunning():
            return

        self.statusBar().showMessage(f"Остановка задачи: {task_name}...")
        task.requestInterruption()
        task.quit()

        # Most operations end normally. The timeout prevents DevHub from
        # remaining in Windows Task Manager because of a blocked worker.
        if not task.wait(3000):
            task.terminate()
            task.wait(1000)

    def shutdown(self) -> None:
        if self._shutdown_in_progress:
            return
        self._shutdown_in_progress = True
        self.exit_button.setEnabled(False)
        self.runtime_timer.stop()

        self._stop_task(self.current_git_task, "Git")
        self._stop_task(self.current_github_task, "GitHub")

        if self.devadvisor_window is not None:
            self.devadvisor_window.close()

        research_window = getattr(self, "research_evolution_window", None)
        if research_window is not None:
            research_window.close()

        app = QApplication.instance()
        if app is not None:
            app.closeAllWindows()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.shutdown()
        event.accept()


def install_research_evolution_center(window: MainWindow) -> None:
    window.research_evolution_window = None

    def open_center() -> None:
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
    app.aboutToQuit.connect(window.shutdown)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
