import json
import urllib.request
from dataclasses import dataclass, field


@dataclass(slots=True)
class StarredRepository:
    full_name: str
    name: str
    owner: str
    description: str = ""
    html_url: str = ""
    clone_url: str = ""
    default_branch: str = "main"
    language: str = ""
    license_name: str = ""
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    updated_at: str = ""
    topics: list[str] = field(default_factory=list)


@dataclass
class GitHubStats:
    repositories: int = 0
    stars: int = 0
    username: str = ""
    starred_repositories: list[StarredRepository] = field(default_factory=list)


class GitHubProvider:
    """Public GitHub provider used by DevHub Alpha."""

    def __init__(self, username: str):
        self.username = username.strip()

    def get_stats(self) -> GitHubStats:
        if not self.username:
            return GitHubStats(username="")

        starred = self._get_starred_repositories()
        return GitHubStats(
            repositories=self._get_public_repository_count(),
            stars=len(starred),
            username=self.username,
            starred_repositories=starred,
        )

    def _get_public_repository_count(self) -> int:
        try:
            data = self._get_json(f"https://api.github.com/users/{self.username}")
            return int(data.get("public_repos", 0))
        except Exception:
            return 0

    def _get_starred_repositories(self) -> list[StarredRepository]:
        result: list[StarredRepository] = []
        page = 1

        while True:
            url = (
                f"https://api.github.com/users/{self.username}/starred"
                f"?per_page=100&page={page}"
            )
            try:
                data = self._get_json(url)
            except Exception:
                break

            if not isinstance(data, list) or not data:
                break

            for item in data:
                owner = item.get("owner") or {}
                license_data = item.get("license") or {}
                result.append(
                    StarredRepository(
                        full_name=str(item.get("full_name", "")),
                        name=str(item.get("name", "")),
                        owner=str(owner.get("login", "")),
                        description=str(item.get("description") or ""),
                        html_url=str(item.get("html_url", "")),
                        clone_url=str(item.get("clone_url", "")),
                        default_branch=str(item.get("default_branch") or "main"),
                        language=str(item.get("language") or ""),
                        license_name=str(license_data.get("spdx_id") or license_data.get("name") or ""),
                        stars=int(item.get("stargazers_count", 0)),
                        forks=int(item.get("forks_count", 0)),
                        open_issues=int(item.get("open_issues_count", 0)),
                        updated_at=str(item.get("updated_at") or ""),
                        topics=[str(topic) for topic in item.get("topics", [])],
                    )
                )

            if len(data) < 100:
                break
            page += 1

        return result

    def _get_json(self, url: str):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "DevHub-Alpha",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
