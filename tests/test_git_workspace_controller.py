from pathlib import Path
from types import SimpleNamespace

from app.workspaces.git import controller as controller_module
from app.workspaces.git.controller import GitWorkspaceController


def test_scan_builds_repository_rows(monkeypatch, tmp_path: Path) -> None:
    repository = tmp_path / "demo"
    repository.mkdir()

    monkeypatch.setattr(
        controller_module,
        "load_settings",
        lambda: {"workspace_paths": [str(tmp_path)], "exclude_folders": ["Archive"]},
    )
    monkeypatch.setattr(controller_module, "find_repositories", lambda **_: [repository])
    monkeypatch.setattr(
        controller_module,
        "load_project_metadata",
        lambda _: SimpleNamespace(
            name="Demo",
            version="0.1.0",
            status="active",
            description="Test project",
        ),
    )
    monkeypatch.setattr(controller_module, "get_branch", lambda _: "feature/demo")
    monkeypatch.setattr(controller_module, "detect_sync_state", lambda *_: "PUSH_REQUIRED")
    monkeypatch.setattr(controller_module, "get_local_last_commit_date", lambda _: "2026-07-29")
    monkeypatch.setattr(controller_module, "get_remote_last_commit_date", lambda *_: "2026-07-28")

    controller = GitWorkspaceController()

    rows = controller.scan()

    assert controller.repositories == [repository]
    assert rows == [
        {
            "name": "Demo",
            "branch": "feature/demo",
            "sync_state": "Нужно отправить изменения",
            "local_date": "2026-07-29",
            "remote_date": "2026-07-28",
            "version": "0.1.0",
            "status": "active",
            "description": "Test project",
            "path": str(repository),
        }
    ]


def test_scan_uses_empty_exclude_list_when_setting_is_missing(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(controller_module, "load_settings", lambda: {"workspace_paths": []})

    def fake_find_repositories(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(controller_module, "find_repositories", fake_find_repositories)

    controller = GitWorkspaceController()

    assert controller.scan() == []
    assert captured == {"workspace_paths": [], "exclude_folders": []}
