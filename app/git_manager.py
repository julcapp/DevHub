import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter


@dataclass
class RepositoryResult:
    name: str
    path: str
    branch: str = ""
    status: str = "UNKNOWN"
    messages: list[str] = field(default_factory=list)


@dataclass
class SyncSummary:
    total: int = 0
    success: int = 0
    skipped: int = 0
    errors: int = 0
    duration_seconds: float = 0.0


def run_git(repo_path: Path, args: list[str]) -> tuple[str, str, int]:
    result = subprocess.run(
        ["git"] + args,
        cwd=repo_path,
        text=True,
        capture_output=True,
        shell=False
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def find_repositories(
    workspace_paths: list[str],
    exclude_folders: list[str] | None = None
) -> list[Path]:
    repositories = []
    exclude_folders = set(exclude_folders or [])

    for workspace in workspace_paths:
        root = Path(workspace)

        if not root.exists():
            continue

        for item in root.iterdir():
            if item.name in exclude_folders:
                continue

            if item.is_dir() and (item / ".git").exists():
                repositories.append(item)

    return sorted(repositories, key=lambda repo: repo.name.lower())


def get_branch(repo_path: Path) -> str:
    stdout, stderr, code = run_git(repo_path, ["branch", "--show-current"])
    return stdout or "unknown"


def has_local_changes(repo_path: Path) -> bool:
    stdout, stderr, code = run_git(repo_path, ["status", "--porcelain"])
    return bool(stdout)


def get_remote_url(repo_path: Path) -> str:
    stdout, stderr, code = run_git(repo_path, ["remote", "get-url", "origin"])
    return stdout if code == 0 else ""


def get_local_last_commit_date(repo_path: Path) -> str:
    stdout, stderr, code = run_git(repo_path, ["log", "-1", "--format=%ci"])
    return stdout if code == 0 else ""


def get_remote_last_commit_date(repo_path: Path, branch: str) -> str:
    # fetch is intentionally separated from this function; call fetch before comparing.
    remote_ref = f"origin/{branch}"
    stdout, stderr, code = run_git(repo_path, ["log", remote_ref, "-1", "--format=%ci"])
    return stdout if code == 0 else ""


def get_ahead_behind(repo_path: Path, branch: str) -> tuple[int, int]:
    remote_ref = f"origin/{branch}"
    stdout, stderr, code = run_git(
        repo_path,
        ["rev-list", "--left-right", "--count", f"HEAD...{remote_ref}"]
    )

    if code != 0 or not stdout:
        return 0, 0

    parts = stdout.split()
    if len(parts) != 2:
        return 0, 0

    try:
        ahead = int(parts[0])
        behind = int(parts[1])
        return ahead, behind
    except ValueError:
        return 0, 0


def detect_sync_state(repo_path: Path, branch: str) -> str:
    if has_local_changes(repo_path):
        return "COMMIT_REQUIRED"

    ahead, behind = get_ahead_behind(repo_path, branch)

    if ahead > 0 and behind > 0:
        return "DIVERGED"
    if ahead > 0:
        return "PUSH_REQUIRED"
    if behind > 0:
        return "PULL_REQUIRED"
    return "SYNCED"


def read_readme_summary(repo_path: Path, max_chars: int = 180) -> str:
    readme_files = [
        repo_path / "README.md",
        repo_path / "readme.md",
        repo_path / "README.MD"
    ]

    for readme_file in readme_files:
        if readme_file.exists():
            try:
                content = readme_file.read_text(encoding="utf-8", errors="ignore")
                lines = []

                for line in content.splitlines():
                    cleaned = line.strip()

                    if not cleaned:
                        continue
                    if cleaned.startswith("#"):
                        continue
                    if cleaned.startswith("!"):
                        continue
                    if cleaned.startswith("["):
                        continue
                    if cleaned.startswith("---"):
                        continue

                    lines.append(cleaned)

                if not lines:
                    return "README найден, но описание не заполнено"

                summary = " ".join(lines)
                if len(summary) > max_chars:
                    summary = summary[:max_chars].rstrip() + "..."

                return summary

            except Exception as error:
                return f"Ошибка чтения README: {error}"

    return "README.md не найден"


def run_repository_command(repo_path: Path, command: list[str]) -> RepositoryResult:
    result = RepositoryResult(name=repo_path.name, path=str(repo_path))
    result.branch = get_branch(repo_path)
    result.messages.append(f"Repository: {repo_path.name}")
    result.messages.append(f"Path: {repo_path}")
    result.messages.append(f"Branch: {result.branch}")
    result.messages.append(f"> git {' '.join(command)}")

    stdout, stderr, code = run_git(repo_path, command)

    if stdout:
        result.messages.append(stdout)
    if stderr:
        result.messages.append(stderr)

    if code == 0:
        result.status = "SUCCESS"
        result.messages.append("STATUS: SUCCESS")
    else:
        result.status = "ERROR"
        result.messages.append(f"ERROR: command failed with code {code}")

    return result


def sync_repository(repo_path: Path, allowed_branches: list[str]) -> RepositoryResult:
    result = RepositoryResult(name=repo_path.name, path=str(repo_path))

    result.messages.append(f"Repository: {repo_path.name}")
    result.messages.append(f"Path: {repo_path}")

    branch = get_branch(repo_path)
    result.branch = branch
    result.messages.append(f"Branch: {branch}")

    if branch not in allowed_branches:
        result.status = "SKIPPED"
        result.messages.append(f"WARNING: skipped, branch '{branch}' is not allowed")
        return result

    if has_local_changes(repo_path):
        result.status = "SKIPPED"
        result.messages.append("WARNING: skipped, local changes found")
        return result

    commands = [["fetch", "--prune"], ["pull"], ["push"]]

    for command in commands:
        command_text = "git " + " ".join(command)
        result.messages.append(f"> {command_text}")

        stdout, stderr, code = run_git(repo_path, command)

        if stdout:
            result.messages.append(stdout)
        if stderr:
            result.messages.append(stderr)

        if code != 0:
            result.status = "ERROR"
            result.messages.append(f"ERROR: command failed with code {code}")
            return result

    result.status = "SUCCESS"
    result.messages.append("STATUS: SUCCESS")
    return result


def sync_all_repositories(
    workspace_paths: list[str],
    allowed_branches: list[str],
    exclude_folders: list[str] | None = None
) -> tuple[list[RepositoryResult], SyncSummary]:
    start = perf_counter()

    repositories = find_repositories(
        workspace_paths=workspace_paths,
        exclude_folders=exclude_folders
    )

    results = []
    summary = SyncSummary(total=len(repositories))

    for repo in repositories:
        repo_result = sync_repository(repo_path=repo, allowed_branches=allowed_branches)
        results.append(repo_result)

        if repo_result.status == "SUCCESS":
            summary.success += 1
        elif repo_result.status == "SKIPPED":
            summary.skipped += 1
        elif repo_result.status == "ERROR":
            summary.errors += 1

    summary.duration_seconds = round(perf_counter() - start, 2)
    return results, summary


def format_result(result: RepositoryResult) -> list[str]:
    lines = ["", "=" * 70, f"{result.name} [{result.status}]", "=" * 70]
    lines.extend(result.messages)
    return lines


def format_summary(summary: SyncSummary) -> list[str]:
    return [
        "",
        "=" * 70,
        "Synchronization summary",
        "=" * 70,
        f"Repositories: {summary.total}",
        f"SUCCESS: {summary.success}",
        f"SKIPPED: {summary.skipped}",
        f"ERROR: {summary.errors}",
        f"Duration: {summary.duration_seconds} sec",
        "=" * 70
    ]
