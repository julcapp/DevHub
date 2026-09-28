from pathlib import Path

from app.workspaces.stars.store import StarsStore
from app.workspaces.stars.workspace import ResearchStatus, StarredRepository


def test_stars_store_roundtrip(tmp_path: Path) -> None:
    store = StarsStore(tmp_path)
    repo = StarredRepository(
        full_name="example/project",
        description="Reference",
        status=ResearchStatus.CANDIDATE,
        notes="Проверить архитектуру",
    )
    store.save([repo])
    loaded = store.load()
    assert loaded["example/project"].status is ResearchStatus.CANDIDATE
    assert loaded["example/project"].notes == "Проверить архитектуру"


def test_remote_merge_preserves_local_decisions(tmp_path: Path) -> None:
    store = StarsStore(tmp_path)
    store.save([StarredRepository(
        full_name="example/project",
        status=ResearchStatus.ADOPTED,
        notes="Использовать как reference",
    )])
    merged = store.merge_remote([StarredRepository(
        full_name="example/project",
        description="Updated from GitHub",
    )])
    assert merged[0].description == "Updated from GitHub"
    assert merged[0].status is ResearchStatus.ADOPTED
    assert merged[0].notes == "Использовать как reference"
