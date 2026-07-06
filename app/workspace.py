from __future__ import annotations

import os
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


DEFAULT_EXCLUDE_FOLDERS = [
    "Archive",
    "Temp",
    "*_OLD",
    "*_BACKUP",
    "*_ARCHIVE",
    ".archive",
    "backup",
    "old",
]


@dataclass
class WorkspaceConfig:
    root: Path
    exclude_folders: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_FOLDERS.copy())
    source: str = "auto"

    @property
    def workspace_paths(self) -> list[str]:
        return [str(self.root)]


def _looks_like_workspace(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False

    if (path / ".devhub-workspace").exists():
        return True

    expected = {"DevHub", "DevHub-Platform", "DevHub-Packages"}
    existing = {item.name for item in path.iterdir() if item.is_dir()}
    return len(expected.intersection(existing)) >= 2


def _contains_git_repositories(path: Path) -> bool:
    """
    Checks only direct children.

    This is intentional: DevHub Alpha scans predictable top-level project folders
    and does not perform expensive recursive discovery.
    """
    if not path.exists() or not path.is_dir():
        return False

    try:
        for item in path.iterdir():
            if item.is_dir() and (item / ".git").exists():
                return True
    except OSError:
        return False

    return False


def _resolve_development_root(base_dir: Path) -> tuple[Path, str] | None:
    """
    Resolves the real repository root for the Development Edition.

    Common layout:

        GitHub/
        ├── CMK_Atom/
        ├── PracticAI/
        └── DevHub-Workspace/
            ├── DevHub/
            ├── DevHub-Platform/
            └── DevHub-Packages/

    When DevHub is launched from inside DevHub-Workspace/DevHub, the old logic
    selected DevHub-Workspace as the root and hid repositories located next to it.
    This resolver promotes the root to the parent directory when that parent
    contains normal Git repositories.
    """
    parent = base_dir.parent.resolve()
    grandparent = parent.parent.resolve()

    if parent.name == "DevHub-Workspace" and _contains_git_repositories(grandparent):
        return grandparent, "auto:development_root"

    return None


def discover_workspace(base_dir: Path, settings: dict[str, Any] | None = None) -> WorkspaceConfig:
    """
    Determines the repository discovery root without hard-coded user paths.

    Priority:
    1. DEVHUB_WORKSPACE environment variable.
    2. Explicit workspace_root in settings.json.
    3. Development layout root: parent of DevHub-Workspace when repositories live there.
    4. Parent folder that looks like DevHub-Workspace.
    5. First path from workspace_paths.
    6. base_dir as fallback.
    """
    settings = settings or {}

    env_workspace = os.environ.get("DEVHUB_WORKSPACE", "").strip()
    if env_workspace:
        path = Path(env_workspace).expanduser().resolve()
        return WorkspaceConfig(root=path, source="env:DEVHUB_WORKSPACE")

    configured_root = str(settings.get("workspace_root", "")).strip()
    if configured_root:
        path = Path(configured_root).expanduser().resolve()
        return WorkspaceConfig(root=path, source="settings:workspace_root")

    development_root = _resolve_development_root(base_dir)
    if development_root:
        path, source = development_root
        return WorkspaceConfig(root=path, source=source)

    parent = base_dir.parent.resolve()
    if _looks_like_workspace(parent):
        return WorkspaceConfig(root=parent, source="auto:parent_workspace")

    workspace_paths = settings.get("workspace_paths") or []
    if workspace_paths:
        path = Path(workspace_paths[0]).expanduser().resolve()
        return WorkspaceConfig(root=path, source="settings:workspace_paths[0]")

    return WorkspaceConfig(root=base_dir.resolve(), source="fallback:base_dir")


def merge_exclude_folders(settings: dict[str, Any], workspace: WorkspaceConfig) -> list[str]:
    configured = settings.get("exclude_folders") or []
    result: list[str] = []

    for item in [*DEFAULT_EXCLUDE_FOLDERS, *workspace.exclude_folders, *configured]:
        if item and item not in result:
            result.append(item)

    return result


def apply_workspace_settings(settings: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    workspace = discover_workspace(base_dir=base_dir, settings=settings)

    updated = dict(settings)
    updated["workspace_root"] = str(workspace.root)
    updated["workspace_source"] = workspace.source
    updated["workspace_paths"] = workspace.workspace_paths
    updated["exclude_folders"] = merge_exclude_folders(settings, workspace)

    return updated


def is_excluded_folder(folder_name: str, exclude_patterns: list[str] | None = None) -> bool:
    patterns = exclude_patterns or DEFAULT_EXCLUDE_FOLDERS
    normalized = folder_name.strip()

    for pattern in patterns:
        if fnmatch(normalized, pattern):
            return True

    return False
