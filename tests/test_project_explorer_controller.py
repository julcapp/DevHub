import json
from pathlib import Path

import pytest

from app.workspaces.explorer.controller import ProjectExplorerController


def test_list_children_hides_service_directories_and_sorts(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "z_folder").mkdir()
    (tmp_path / "a_folder").mkdir()
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")

    controller = ProjectExplorerController()
    names = [path.name for path in controller.list_children(tmp_path)]

    assert names == ["a_folder", "z_folder", "a.txt", "b.txt"]


def test_preview_formats_json_and_returns_metadata(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"name": "DevHub", "enabled": True}), encoding="utf-8")

    preview = ProjectExplorerController().preview(path)

    assert preview.path == path
    assert preview.kind == "json"
    assert '"name": "DevHub"' in preview.content
    assert preview.line_count > 1
    assert preview.size_bytes == path.stat().st_size


def test_preview_rejects_unsupported_file(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"png")

    with pytest.raises(ValueError, match="Формат файла не поддерживается"):
        ProjectExplorerController().preview(path)


def test_preview_rejects_large_file(tmp_path: Path) -> None:
    path = tmp_path / "large.txt"
    path.write_text("x" * 101, encoding="utf-8")

    with pytest.raises(ValueError, match="Файл слишком большой"):
        ProjectExplorerController().preview(path, max_bytes=100)
