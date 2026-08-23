import json
from pathlib import Path

from app.workspaces.architecture.ci_cache import CICacheManager


def test_ci_cache_prunes_old_runs_and_writes_status(tmp_path: Path) -> None:
    for run_id in (100, 101, 102, 103):
        (tmp_path / f"{run_id}.json").write_text(json.dumps({"run_id": str(run_id)}), encoding="utf-8")
    manager = CICacheManager(max_records=2)
    status = manager.maintain(tmp_path)
    assert status.records == 2
    assert status.removed == 2
    assert (tmp_path / "103.json").exists()
    assert (tmp_path / "102.json").exists()
    assert not (tmp_path / "101.json").exists()
    loaded = manager.load_status(tmp_path)
    assert loaded is not None
    assert loaded.records == 2
    assert loaded.max_records == 2


def test_ci_cache_ignores_metadata_file(tmp_path: Path) -> None:
    manager = CICacheManager(max_records=3)
    manager.maintain(tmp_path)
    assert manager.maintain(tmp_path).records == 0


def test_ci_cache_clear_removes_results_and_metadata(tmp_path: Path) -> None:
    manager = CICacheManager(max_records=3)
    for run_id in (100, 101):
        (tmp_path / f"{run_id}.json").write_text(json.dumps({"run_id": str(run_id)}), encoding="utf-8")
    manager.maintain(tmp_path)
    assert manager.load_status(tmp_path) is not None
    assert manager.clear(tmp_path) == 2
    assert manager.load_status(tmp_path) is None
    assert list(tmp_path.glob("*.json")) == []
