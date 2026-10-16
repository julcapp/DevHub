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


def test_unstar_does_not_delete_research_notes(tmp_path: Path) -> None:
    store = StarsStore(tmp_path)
    store.save([StarredRepository(full_name="example/old", notes="Keep research")])
    merged = store.merge_remote([StarredRepository(full_name="example/new")])
    assert {repo.full_name for repo in merged} == {"example/old", "example/new"}
    assert next(repo for repo in merged if repo.full_name == "example/old").notes == "Keep research"


def test_corrupt_store_is_not_silently_overwritten(tmp_path: Path) -> None:
    import pytest

    store = StarsStore(tmp_path)
    store.path.write_text("{invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="Не удалось прочитать"):
        store.merge_remote([StarredRepository(full_name="example/new")])
    assert store.path.read_text(encoding="utf-8") == "{invalid"
