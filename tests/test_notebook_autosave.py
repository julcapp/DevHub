import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from app.workspaces.notebook.notebook_workspace import EngineeringNotebookWorkspace


def test_notebook_autosave_and_category_switch(tmp_path):
    app = QApplication.instance() or QApplication([])
    workspace = EngineeringNotebookWorkspace()
    workspace.set_project(tmp_path)
    document = workspace.controller.create_document("Идеи", "Голосовая мысль")
    workspace._reload_documents("Идеи")
    workspace._select_document(document.path)
    workspace.editor.setPlainText("# Голосовая мысль\n\nНовая идея через Handy")
    assert workspace._autosave_timer.isActive()
    workspace.categories.setCurrentRow(1)
    assert "Новая идея через Handy" in document.path.read_text(encoding="utf-8")
    assert workspace.current_document is None
    assert not workspace._autosave_timer.isActive()
    workspace.close()


def test_notebook_autosave_after_edit(tmp_path):
    app = QApplication.instance() or QApplication([])
    workspace = EngineeringNotebookWorkspace()
    workspace.set_project(tmp_path)
    document = workspace.controller.create_document("Идеи", "Проверка")
    workspace._reload_documents("Идеи")
    workspace._select_document(document.path)
    workspace.editor.insertPlainText("Текст диктовки")
    workspace._autosave_document()
    assert "Текст диктовки" in document.path.read_text(encoding="utf-8")
    assert workspace.save_status.text() == "Все изменения сохранены"
    workspace.close()


def test_autosave_preserves_cursor_and_document_selection(tmp_path):
    app = QApplication.instance() or QApplication([])
    workspace = EngineeringNotebookWorkspace()
    workspace.set_project(tmp_path)
    document = workspace.controller.create_document("Идеи", "Позиция курсора")
    workspace._reload_documents("Идеи")
    workspace._select_document(document.path)
    workspace.editor.setPlainText("Начало текста")
    cursor = workspace.editor.textCursor()
    cursor.setPosition(3)
    workspace.editor.setTextCursor(cursor)
    selected = workspace.documents.currentItem()
    workspace._autosave_document()
    assert workspace.editor.textCursor().position() == 3
    assert workspace.documents.currentItem() is selected
    assert workspace.current_document == document.path
    workspace.close()
