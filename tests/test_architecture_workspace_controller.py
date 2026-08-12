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
    assert summary.cycles == ()
    assert summary.warnings == ()


def test_architecture_summary_detects_dependency_cycle(tmp_path: Path) -> None:
    package = tmp_path / "app"
    package.mkdir()
    (package / "a.py").write_text("import app.b\n", encoding="utf-8")
    (package / "b.py").write_text("import app.c\n", encoding="utf-8")
    (package / "c.py").write_text("import app.a\n", encoding="utf-8")

    summary = ArchitectureWorkspaceController().analyze(tmp_path)

    assert summary.internal_dependencies == 3
    assert summary.cycles == (("app.a", "app.b", "app.c"),)
    assert summary.warnings == (
        "Циклическая зависимость: app.a → app.b → app.c → app.a",
    )


def test_architecture_summary_warns_about_high_coupling(tmp_path: Path) -> None:
    package = tmp_path / "app"
    package.mkdir()
    for name in "bcdef":
        (package / f"{name}.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "a.py").write_text(
        "import app.b\nimport app.c\nimport app.d\nimport app.e\nimport app.f\n",
        encoding="utf-8",
    )

    summary = ArchitectureWorkspaceController().analyze(tmp_path)

    assert summary.internal_dependencies == 5
    assert "Высокая связанность: app.a зависит от 5 внутренних модулей" in summary.warnings


def test_architecture_summary_calculates_module_risk(tmp_path: Path) -> None:
    package = tmp_path / "app"
    package.mkdir()
    for name in "bcdefg":
        (package / f"{name}.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "a.py").write_text(
        "import app.b\nimport app.c\nimport app.d\nimport app.e\nimport app.f\nimport app.g\n"
        "class Service:\n"
        "    def run(self):\n"
        "        return 1\n",
        encoding="utf-8",
    )

    summary = ArchitectureWorkspaceController().analyze(tmp_path)
    module = next(item for item in summary.module_details if item.name == "app.a")

    assert module.coupling == 6
    assert module.risk_score >= 60
    assert module.risk_level == "Высокий"
    assert any("Высокий архитектурный риск: app.a" in warning for warning in summary.warnings)
