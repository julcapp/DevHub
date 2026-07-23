import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from app.research_evolution_window import ResearchEvolutionWindow
from app.ui import MainWindow


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


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    install_research_evolution_center(window)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
