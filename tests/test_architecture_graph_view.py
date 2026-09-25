import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.controller import ArchitectureSummary, ModuleArchitecture
from app.workspaces.architecture.graph_view import ArchitectureGraphView


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _summary(*, cycles: tuple[tuple[str, ...], ...] = ()) -> ArchitectureSummary:
    return ArchitectureSummary(
        project_name="demo", project_path="/demo", files=2, folders=1,
        modules=2, classes=0, methods=0, functions=0, imports=2,
        internal_dependencies=2 if cycles else 1, nodes_total=4, edges_total=4,
        dependencies=("app.a → app.b",), cycles=cycles, warnings=(),
        module_details=(
            ModuleArchitecture("app.a", "app/a.py", ("app.b",), ("app.b",) if cycles else (), ()),
            ModuleArchitecture("app.b", "app/b.py", ("app.a",) if cycles else (), ("app.a",), ()),
        ),
    )


def test_graph_view_renders_modules_and_dependencies() -> None:
    _app(); view = ArchitectureGraphView(); view.show_summary(_summary())
    labels = [item.text() for item in view.scene().items() if hasattr(item, "text")]
    assert "app.a" in labels and "app.b" in labels
    assert len(view.scene().items()) >= 5


def test_graph_view_selects_module_and_highlights_relations() -> None:
    _app(); view = ArchitectureGraphView(); view.show_summary(_summary()); view.select_module("app.a")
    assert view._nodes["app.a"].isSelected()
    assert view._edges[0][2].pen().widthF() == 2.4


def test_graph_view_marks_cycle_modules() -> None:
    _app(); view = ArchitectureGraphView(); view.show_summary(_summary(cycles=(("app.a", "app.b"),)))
    assert view._cycle_modules == {"app.a", "app.b"}
    assert view._nodes["app.a"].pen().widthF() == 2.5
