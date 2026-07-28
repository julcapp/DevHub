import sys

from PySide6.QtWidgets import QApplication

from app.ui import MainWindow
from core.bootstrap.bootstrap import Bootstrap


def main() -> None:
    app = QApplication(sys.argv)
    bootstrap = Bootstrap(MainWindow)
    app.aboutToQuit.connect(bootstrap.shutdown)

    window = bootstrap.run()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
