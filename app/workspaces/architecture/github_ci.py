from __future__ import annotations

import configparser
import json
import os
import re
import urllib.error
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path


class GitHubCIError(RuntimeError):
    pass


def repository_from_git_config(root: Path) -> str | None:
    config_path = root.resolve() / ".git" / "config"
    if not config_path.exists():
        return None
    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")
    section = 'remote "origin"'
    if not parser.has_section(section):
        return None
    url = parser.get(section, "url", fallback="").strip()
    patterns = (
        r"github\.com[:/](?P<repo>[^/\s]+/[^/\s]+?)(?:\.git)?$",
        r"https?://github\.com/(?P<repo>[^/\s]+/[^/\s]+?)(?:\.git)?$",
    )
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group("repo")
    return None


class GitHubCIArtifactClient:
    API = "https://api.github.com"

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

    def _request(self, url: str) -> bytes:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "DevHub"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
                return response.read()
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            raise GitHubCIError(f"GitHub API недоступен: {error}") from error

    def download_quality_gate_history(self, repository: str, destination: Path, limit: int = 20) -> int:
        destination.mkdir(parents=True, exist_ok=True)
        runs_url = f"{self.API}/repos/{repository}/actions/workflows/tests.yml/runs?event=pull_request&status=completed&per_page={limit}"
        runs = json.loads(self._request(runs_url)).get("workflow_runs", [])
        saved = 0
        for run in runs:
            run_id = int(run["id"])
            artifacts_url = f"{self.API}/repos/{repository}/actions/runs/{run_id}/artifacts?name=architecture-quality-gate"
            artifacts = json.loads(self._request(artifacts_url)).get("artifacts", [])
            if not artifacts:
                continue
            archive = self._request(artifacts[0]["archive_download_url"])
            with zipfile.ZipFile(BytesIO(archive)) as bundle:
                candidates = [name for name in bundle.namelist() if name.endswith("architecture-quality-gate.json")]
                if not candidates:
                    continue
                payload = json.loads(bundle.read(candidates[0]).decode("utf-8"))
            payload.setdefault("run_id", str(run_id))
            payload.setdefault("commit_sha", str(run.get("head_sha", "")))
            output = destination / f"{run_id}.json"
            output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            saved += 1
        return saved
