from __future__ import annotations

import json
from pathlib import Path

from app.models.technology_profile import TechnologyProfile


class TechnologyProfileService:
    """Persists DevHub-specific knowledge separately from GitHub source data."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or Path(".devhub") / "technology_profiles.json"

    def load_all(self) -> dict[str, TechnologyProfile]:
        if not self.storage_path.exists():
            return {}
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        profiles: dict[str, TechnologyProfile] = {}
        for item in raw if isinstance(raw, list) else []:
            try:
                profile = TechnologyProfile.from_dict(item)
            except (TypeError, ValueError):
                continue
            if profile.repository_full_name:
                profiles[profile.repository_full_name] = profile
        return profiles

    def save_all(self, profiles: dict[str, TechnologyProfile]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [profile.to_dict() for profile in profiles.values()]
        self.storage_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_or_create(
        self,
        profiles: dict[str, TechnologyProfile],
        repository_full_name: str,
    ) -> TechnologyProfile:
        profile = profiles.get(repository_full_name)
        if profile is None:
            profile = TechnologyProfile(repository_full_name=repository_full_name)
            profiles[repository_full_name] = profile
        return profile
