from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum


class TechnologyStatus(StrEnum):
    DISCOVERED = "Обнаружена"
    STUDYING = "Изучается"
    PLANNED = "Планируется"
    IN_USE = "Используется"
    INTERNAL_FORK = "Внутренний Fork"
    ARCHIVED = "Архив"
    REJECTED = "Не рекомендована"


@dataclass(slots=True)
class TechnologyScore:
    stability: int = 0
    activity: int = 0
    documentation: int = 0
    security: int = 0
    compatibility: int = 0
    internal_experience: int = 0

    def total(self) -> float:
        weighted = (
            self.stability * 0.20
            + self.activity * 0.15
            + self.documentation * 0.10
            + self.security * 0.15
            + self.compatibility * 0.20
            + self.internal_experience * 0.20
        )
        return round(weighted / 10, 1)


@dataclass(slots=True)
class TechnologyProfile:
    repository_full_name: str
    status: TechnologyStatus = TechnologyStatus.STUDYING
    internal_notes: str = ""
    why_selected: list[str] = field(default_factory=list)
    used_in_projects: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)
    internet_summary: str = ""
    security_notes: str = ""
    compatibility_notes: str = ""
    fork_repository: str = ""
    evolution_branch: str = ""
    upstream_repository: str = ""
    score: TechnologyScore = field(default_factory=TechnologyScore)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "TechnologyProfile":
        score = TechnologyScore(**data.get("score", {}))
        return cls(
            repository_full_name=str(data.get("repository_full_name", "")),
            status=TechnologyStatus(data.get("status", TechnologyStatus.STUDYING.value)),
            internal_notes=str(data.get("internal_notes", "")),
            why_selected=list(data.get("why_selected", [])),
            used_in_projects=list(data.get("used_in_projects", [])),
            source_urls=list(data.get("source_urls", [])),
            internet_summary=str(data.get("internet_summary", "")),
            security_notes=str(data.get("security_notes", "")),
            compatibility_notes=str(data.get("compatibility_notes", "")),
            fork_repository=str(data.get("fork_repository", "")),
            evolution_branch=str(data.get("evolution_branch", "")),
            upstream_repository=str(data.get("upstream_repository", "")),
            score=score,
        )
