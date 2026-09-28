from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.workspaces.stars.workspace import StarredRepository


class GitHubStarsError(RuntimeError):
    pass


@dataclass(slots=True)
class GitHubStarsClient:
    """Минимальный read-only клиент GitHub Stars.

    Токен берётся только из окружения DEVHUB_GITHUB_TOKEN/GITHUB_TOKEN и
    никогда не хранится в репозитории или stars.json.
    """

    token: str | None = None
    api_url: str = "https://api.github.com"

    def __post_init__(self) -> None:
        if self.token is None:
            self.token = os.getenv("DEVHUB_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def fetch_all(self) -> list[StarredRepository]:
        if not self.token:
            raise GitHubStarsError(
                "GitHub не авторизован. Настройте DEVHUB_GITHUB_TOKEN с read-only доступом."
            )
        repositories: list[StarredRepository] = []
        page = 1
        while True:
            url = f"{self.api_url}/user/starred?per_page=100&page={page}"
            request = Request(
                url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self.token}",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "DevHub-Stars",
                },
            )
            try:
                with urlopen(request, timeout=15) as response:
                    payload = json.load(response)
            except HTTPError as error:
                if error.code in (401, 403):
                    raise GitHubStarsError(
                        "GitHub отклонил авторизацию. Проверьте токен и его права."
                    ) from error
                raise GitHubStarsError(f"GitHub API: HTTP {error.code}.") from error
            except (URLError, TimeoutError, OSError) as error:
                raise GitHubStarsError(f"GitHub API недоступен: {error}.") from error

            if not isinstance(payload, list):
                raise GitHubStarsError("GitHub API вернул неожиданный формат данных.")
            for item in payload:
                license_data = item.get("license") or {}
                repositories.append(
                    StarredRepository(
                        full_name=item.get("full_name", ""),
                        description=item.get("description") or "",
                        url=item.get("html_url") or "",
                        language=item.get("language") or "",
                        license_name=license_data.get("spdx_id") or "",
                    )
                )
            if len(payload) < 100:
                break
            page += 1
        return [repo for repo in repositories if repo.full_name]
