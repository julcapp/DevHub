import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from importlib import import_module

# Keep test-only imports outside the production dependency graph.
EngineeringNotebookWorkspace = import_module(
    "app.workspaces.notebook.notebook_workspace"
).EngineeringNotebookWorkspace


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


def test_voice_recording_starts_transcription_without_counter_crash(tmp_path, monkeypatch):
    from app.workspaces.notebook.microphone import MicrophoneRecorder
    from app.workspaces.notebook import notebook_workspace

    app = QApplication.instance() or QApplication([])
    workspace = EngineeringNotebookWorkspace()
    workspace.set_project(tmp_path)
    document = workspace.controller.create_document("Идеи", "Диктовка")
    workspace._reload_documents("Идеи")
    workspace._select_document(document.path)

    class FakeRecorder:
        def start(self):
            pass

        def stop(self):
            audio = tmp_path / "voice.wav"
            audio.write_bytes(b"fake")
            return audio

        def cancel(self):
            pass

    class FakeWorker:
        def __init__(self, path):
            self.path = path
            self.completed = type("Signal", (), {"connect": lambda self, cb: None})()
            self.failed = type("Signal", (), {"connect": lambda self, cb: None})()
            self.finished = type("Signal", (), {"connect": lambda self, cb: None})()

        def start(self):
            pass

        def isRunning(self):
            return False

    monkeypatch.setattr(notebook_workspace, "TranscriptionWorker", FakeWorker)
    monkeypatch.setattr(MicrophoneRecorder, "start", lambda self: None)
    monkeypatch.setattr(MicrophoneRecorder, "stop", lambda self: tmp_path / "voice.wav")
    workspace.toggle_local_recording()
    workspace.toggle_local_recording()
    assert workspace._transcription_document == document.path
    assert workspace._transcription_worker is not None
    workspace._transcription_worker = None
    workspace.close()
