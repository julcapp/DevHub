import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from app.workspaces.projects_workspace import ProjectsWorkspace


def test_project_search_filters_by_name_and_language(monkeypatch):
    monkeypatch.setattr(ProjectsWorkspace, "reload", lambda self: None)
    app = QApplication.instance() or QApplication([])
    workspace = ProjectsWorkspace()
    workspace.loaded([
        {"full_name": "julcapp/DevHub", "description": "Engineering OS", "language": "Python"},
        {"full_name": "julcapp/website", "description": "Public site", "language": "TypeScript"},
    ])
    workspace.search.setText("python")
    assert workspace.items.count() == 1
    assert "DevHub" in workspace.items.item(0).text()
    workspace.search.setText("missing")
    assert workspace.items.count() == 0
    workspace.close()
