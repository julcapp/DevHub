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


def test_project_kind_filter(monkeypatch):
    monkeypatch.setattr(ProjectsWorkspace, "reload", lambda self: None)
    app = QApplication.instance() or QApplication([])
    workspace = ProjectsWorkspace()
    workspace.loaded([
        {"full_name": "julcapp/original", "fork": False},
        {"full_name": "julcapp/forked", "fork": True},
    ])
    workspace.kind_filter.setCurrentIndex(1)
    assert workspace.items.count() == 1
    assert "original" in workspace.items.item(0).text()
    workspace.kind_filter.setCurrentIndex(2)
    assert workspace.items.count() == 1
    assert "forked" in workspace.items.item(0).text()
    workspace.close()


def test_failed_refresh_preserves_loaded_projects(monkeypatch):
    monkeypatch.setattr(ProjectsWorkspace, "reload", lambda self: None)
    app = QApplication.instance() or QApplication([])
    workspace = ProjectsWorkspace()
    workspace.loaded([{"full_name": "julcapp/DevHub", "fork": False}])
    workspace.failed("Нет связи с GitHub.")
    assert workspace.items.count() == 1
    assert "Нет связи" in workspace.status.text()
    workspace.close()


def test_project_sorting_by_stars_and_name(monkeypatch):
    monkeypatch.setattr(ProjectsWorkspace, "reload", lambda self: None)
    app = QApplication.instance() or QApplication([])
    workspace = ProjectsWorkspace()
    workspace.loaded([
        {"full_name": "julcapp/zeta", "stargazers_count": 2, "updated_at": "2026-01-01T00:00:00Z"},
        {"full_name": "julcapp/alpha", "stargazers_count": 20, "updated_at": "2025-01-01T00:00:00Z"},
    ])
    workspace.sort_filter.setCurrentIndex(2)
    assert "alpha" in workspace.items.item(0).text()
    workspace.sort_filter.setCurrentIndex(1)
    assert "alpha" in workspace.items.item(0).text()
    workspace.sort_filter.setCurrentIndex(0)
    assert "zeta" in workspace.items.item(0).text()
    workspace.close()
