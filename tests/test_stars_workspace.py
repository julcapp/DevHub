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
