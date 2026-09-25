from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.workspaces.stars.workspace import ResearchStatus, StarredRepository


class StarsStore:
    """Локальное хранение пользовательских решений по GitHub Stars."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".devhub")
        self.path = self.root / "stars.json"

    def load(self) -> dict[str, StarredRepository]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        result: dict[str, StarredRepository] = {}
        for item in raw.get("repositories", []):
            try:
                repo = StarredRepository(
                    full_name=item["full_name"],
                    description=item.get("description", ""),
                    url=item.get("url", ""),
                    language=item.get("language", ""),
                    license_name=item.get("license_name", ""),
                    status=ResearchStatus(item.get("status", ResearchStatus.NEW.value)),
                    notes=item.get("notes", ""),
                )
            except (KeyError, ValueError, TypeError):
                continue
            result[repo.full_name] = repo
        return result

    def save(self, repositories: list[StarredRepository]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "repositories": []}
        for repo in repositories:
            item = asdict(repo)
            item["status"] = repo.status.value
            payload["repositories"].append(item)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def merge_remote(self, remote: list[StarredRepository]) -> list[StarredRepository]:
        local = self.load()
        merged: list[StarredRepository] = []
        for repo in remote:
            saved = local.get(repo.full_name)
            if saved is not None:
                repo.status = saved.status
                repo.notes = saved.notes
            merged.append(repo)
        return merged
