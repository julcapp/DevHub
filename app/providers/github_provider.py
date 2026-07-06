import json
import urllib.request
from dataclasses import dataclass


@dataclass
class GitHubStats:
    repositories: int = 0
    stars: int = 0
    username: str = ""


class GitHubProvider:
    """
    Минимальный GitHub Provider для Alpha.

    Работает без токена и получает только публичные данные:
    - количество публичных репозиториев пользователя;
    - количество starred repositories.

    Для приватных репозиториев и расширенной аналитики позже будет добавлен GitHub token.
    """

    def __init__(self, username: str):
        self.username = username.strip()

    def get_stats(self) -> GitHubStats:
        if not self.username:
            return GitHubStats(username="")

        repositories = self._get_public_repository_count()
        stars = self._get_star_count()

        return GitHubStats(
            repositories=repositories,
            stars=stars,
            username=self.username,
        )

    def _get_public_repository_count(self) -> int:
        url = f"https://api.github.com/users/{self.username}"

        try:
            data = self._get_json(url)
            return int(data.get("public_repos", 0))
        except Exception:
            return 0

    def _get_star_count(self) -> int:
        total = 0
        page = 1

        try:
            while True:
                url = (
                    f"https://api.github.com/users/{self.username}/starred"
                    f"?per_page=100&page={page}"
                )
                data = self._get_json(url)

                if not isinstance(data, list) or not data:
                    break

                total += len(data)

                if len(data) < 100:
                    break

                page += 1

            return total

        except Exception:
            return 0

    def _get_json(self, url: str):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "DevHub-Alpha",
            },
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))