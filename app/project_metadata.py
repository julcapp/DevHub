import json
from dataclasses import dataclass, field
from pathlib import Path

from app.git_manager import read_readme_summary


@dataclass
class ProjectMetadata:
    name: str
    code: str
    description: str
    version: str = ""
    status: str = "unknown"
    priority: str = "normal"
    project_type: str = "unknown"
    source: str = "README"
    tags: list[str] = field(default_factory=list)


def _safe_get(data: dict, *keys: str, default=""):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def load_project_metadata(repo_path: Path) -> ProjectMetadata:
    project_json = repo_path / ".devhub" / "project.json"

    if project_json.exists():
        try:
            data = json.loads(project_json.read_text(encoding="utf-8"))
            project = data.get("project", {})

            return ProjectMetadata(
                name=project.get("name") or repo_path.name,
                code=project.get("code") or repo_path.name,
                description=project.get("description") or read_readme_summary(repo_path),
                version=project.get("version", ""),
                status=project.get("status", "unknown"),
                priority=project.get("priority", "normal"),
                project_type=project.get("type", "unknown"),
                source="DHMS",
                tags=data.get("tags", []) if isinstance(data.get("tags", []), list) else []
            )
        except Exception:
            pass

    return ProjectMetadata(
        name=repo_path.name,
        code=repo_path.name,
        description=read_readme_summary(repo_path),
        source="README"
    )
