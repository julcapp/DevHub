from app.status import ApplicationStatus


class StatusService:
    """
    Единая точка управления состоянием DevHub.

    UI ничего не вычисляет самостоятельно.
    Все изменения проходят через StatusService.
    """

    def __init__(self):
        self.status = ApplicationStatus()

    # ---------------------------------------------------------
    # Состояние приложения
    # ---------------------------------------------------------

    def ready(self):
        self.status.set_ready()

    def working(self):
        self.status.set_busy()

    def error(self, message: str):
        self.status.set_error(message)

    # ---------------------------------------------------------
    # Репозитории
    # ---------------------------------------------------------

    def update_scan(
        self,
        repositories: int,
        scan_time: float,
        slowest_repo: str,
        slowest_time: float,
    ):
        self.status.update_scan(
            repositories,
            scan_time,
            slowest_repo,
            slowest_time,
        )

    def update_github(
        self,
        repositories: int,
        stars: int,
    ):
        self.status.update_github(
            repositories,
            stars,
        )

    # ---------------------------------------------------------
    # Получение состояния
    # ---------------------------------------------------------

    @property
    def data(self):
        return self.status