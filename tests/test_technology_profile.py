from pathlib import Path

from app.models.technology_profile import (
    TechnologyProfile,
    TechnologyScore,
    TechnologyStatus,
)
from app.services.technology_profile_service import TechnologyProfileService


def test_weighted_technology_score() -> None:
    score = TechnologyScore(
        stability=80,
        activity=90,
        documentation=70,
        security=80,
        compatibility=100,
        internal_experience=60,
    )
    assert score.total() == 8.0


def test_profile_roundtrip(tmp_path: Path) -> None:
    service = TechnologyProfileService(tmp_path / "profiles.json")
    profile = TechnologyProfile(
        repository_full_name="owner/project",
        status=TechnologyStatus.PLANNED,
        fork_repository="julcapp/project",
        evolution_branch="devhub/evolution-project",
    )
    service.save_all({profile.repository_full_name: profile})

    loaded = service.load_all()["owner/project"]
    assert loaded.status is TechnologyStatus.PLANNED
    assert loaded.fork_repository == "julcapp/project"
    assert loaded.evolution_branch == "devhub/evolution-project"
