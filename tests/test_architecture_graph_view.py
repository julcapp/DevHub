import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.controller import ArchitectureSummary, ModuleArchitecture
from app.workspaces.architecture.graph_view import ArchitectureGraphView


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_graph_view_renders_modules_and_dependencies() -> None:
    _app()
    summary = ArchitectureSummary(
        project_name="demo", project_path="/demo", files=2, folders=1,
        modules=2, classes=0, methods=0, functions=0, imports=1,
        internal_dependencies=1, nodes_total=4, edges_total=3,
        dependencies=("app.a → app.b",), cycles=(), warnings=(),
        module_details=(
            ModuleArchitecture("app.a", "app/a.py", ("app.b",), (), ()),
            ModuleArchitecture("app.b", "app/b.py", (), ("app.a",), ()),
        ),
    )
    view = ArchitectureGraphView()
    view.show_summary(summary)

    labels = [item.text() for item in view.scene().items() if hasattr(item, "text")]
    assert "app.a" in labels
    assert "app.b" in labels
    assert len(view.scene().items()) >= 5
