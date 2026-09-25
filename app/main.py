import sys

from PySide6.QtWidgets import QApplication

from app.platform import PlatformKernel
from app.shell import DevHubShell


def main() -> None:
    application = QApplication(sys.argv)
    application.setApplicationName("DevHub")
    application.setOrganizationName("DevHub")

    kernel = PlatformKernel()
    window = DevHubShell(kernel)
    window.show()
    kernel.start()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()
