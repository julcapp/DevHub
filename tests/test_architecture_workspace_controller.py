from pathlib import Path

from app.workspaces.architecture.controller import ArchitectureWorkspaceController


def test_architecture_summary_reports_internal_dependencies(tmp_path: Path) -> None:
    package = tmp_path / "app"
    package.mkdir()
    (package / "models.py").write_text("class User:\n    pass\n", encoding="utf-8")
    (package / "service.py").write_text(
        "from app import models\n\n"
        "class Service:\n"
        "    def load(self):\n"
        "        return models.User()\n",
        encoding="utf-8",
    )

    summary = ArchitectureWorkspaceController().analyze(tmp_path)

    assert summary.project_name == tmp_path.name
    assert summary.files == 2
    assert summary.modules == 2
    assert summary.classes == 2
    assert summary.methods == 1
    assert summary.internal_dependencies == 1
    assert summary.dependencies == ("app.service → app.models",)
