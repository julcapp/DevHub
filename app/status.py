from dataclasses import dataclass, field
from datetime import datetime
from time import time


@dataclass
class ApplicationStatus:
    # состояние приложения
    current_state: str = "READY"

    # репозитории
    local_repositories: int = 0
    github_repositories: int = 0
    github_stars: int = 0

    # производительность
    last_scan_time: float = 0.0
    slowest_repository: str = ""
    slowest_time: float = 0.0

    # время
    started_at: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)

    # ошибки
    last_error: str = ""

    def set_ready(self):
        self.current_state = "READY"

    def set_busy(self):
        self.current_state = "WORKING"

    def set_error(self, message: str):
        self.current_state = "ERROR"
        self.last_error = message

    def update_scan(
        self,
        repositories: int,
        scan_time: float,
        slowest_repo: str,
        slowest_time: float,
    ):
        self.local_repositories = repositories
        self.last_scan_time = round(scan_time, 3)
        self.slowest_repository = slowest_repo
        self.slowest_time = round(slowest_time, 3)
        self.last_update = datetime.now()

    def update_github(
        self,
        repositories: int,
        stars: int,
    ):
        self.github_repositories = repositories
        self.github_stars = stars
        self.last_update = datetime.now()

    @property
    def uptime(self) -> str:
        seconds = int(time() - self.started_at.timestamp())

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        return f"{hours:02}:{minutes:02}:{secs:02}"

    @property
    def started_string(self) -> str:
        return self.started_at.strftime("%d.%m.%Y %H:%M:%S")

    @property
    def last_update_string(self) -> str:
        return self.last_update.strftime("%H:%M:%S")