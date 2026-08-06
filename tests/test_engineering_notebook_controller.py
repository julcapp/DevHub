from pathlib import Path

import pytest

from app.workspaces.notebook.controller import EngineeringNotebookController


def test_set_project_creates_notebook_structure(tmp_path: Path) -> None:
    controller = EngineeringNotebookController()

    controller.set_project(tmp_path)

    assert (tmp_path / ".devhub" / "ideas").is_dir()
    assert (tmp_path / ".devhub" / "adr").is_dir()
    assert (tmp_path / ".devhub" / "research").is_dir()
    assert (tmp_path / ".devhub" / "decisions").is_dir()
    assert (tmp_path / ".devhub" / "tasks").is_dir()
    assert (tmp_path / ".devhub" / "meetings").is_dir()
    assert (tmp_path / ".devhub" / "drafts").is_dir()


def test_create_load_save_and_delete_document(tmp_path: Path) -> None:
    controller = EngineeringNotebookController()
    controller.set_project(tmp_path)

    document = controller.create_document("Идеи", "Новая идея")

    assert document.path.exists()
    assert document.path.name == "новая-идея.md"
    assert controller.load_document(document.path).title == "Новая идея"

    updated = controller.save_document(document.path, "# Изменённая идея\n\nТекст")
    assert updated.title == "Изменённая идея"
    assert controller.load_document(document.path).content.endswith("Текст")

    controller.delete_document(document.path)
    assert document.path.exists() is False


def test_create_document_uses_unique_path(tmp_path: Path) -> None:
    controller = EngineeringNotebookController()
    controller.set_project(tmp_path)

    first = controller.create_document("ADR", "Выбор базы данных")
    second = controller.create_document("ADR", "Выбор базы данных")

    assert first.path.name == "выбор-базы-данных.md"
    assert second.path.name == "выбор-базы-данных-2.md"


def test_document_outside_notebook_is_rejected(tmp_path: Path) -> None:
    controller = EngineeringNotebookController()
    controller.set_project(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside", encoding="utf-8")

    with pytest.raises(ValueError):
        controller.load_document(outside)
