from __future__ import annotations

from .model import Mission


class MissionRegistry:
    def __init__(self) -> None:
        self._missions: dict[str, Mission] = {}

    def register(self, mission: Mission) -> None:
        if mission.mission_id in self._missions:
            raise ValueError(f"Mission already registered: {mission.mission_id}")
        self._missions[mission.mission_id] = mission

    def get(self, mission_id: str) -> Mission:
        try:
            return self._missions[mission_id]
        except KeyError as exc:
            raise KeyError(f"Unknown mission: {mission_id}") from exc

    def list(self) -> tuple[Mission, ...]:
        return tuple(self._missions.values())
