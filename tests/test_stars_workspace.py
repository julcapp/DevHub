import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.workspaces.stars.store import StarsStore
from app.workspaces.stars.workspace import StarsWorkspace


def test_corrupt_local_store_does_not_crash_workspace(monkeypatch):
    app = QApplication.instance() or QApplication([])
    def invalid_load(self):
        raise ValueError("corrupt JSON")
    monkeypatch.setattr(StarsStore, "load", invalid_load)
    workspace = StarsWorkspace()
    assert "corrupt JSON" in workspace.state_label.text()
    workspace.close()


def test_notes_survive_filter_change(monkeypatch, tmp_path):
    monkeypatch.setattr(StarsStore, "__init__", lambda self: None)
    monkeypatch.setattr(StarsStore, "load", lambda self: {})
    from app.workspaces.stars.workspace import StarredRepository, ResearchStatus
    app = QApplication.instance() or QApplication([])
    workspace = StarsWorkspace()
    workspace.set_repositories([StarredRepository(full_name="owner/one")])
    workspace.list_widget.setCurrentRow(0)
    workspace.notes.setPlainText("Important research")
    workspace.status_combo.setCurrentText(ResearchStatus.CANDIDATE.value)
    workspace.search.setText("no-match")
    assert workspace._repositories[0].notes == "Important research"
    assert workspace._repositories[0].status is ResearchStatus.CANDIDATE
    workspace.close()
