import json
import zipfile
from io import BytesIO
from pathlib import Path

from app.workspaces.architecture.github_ci import GitHubCIArtifactClient, repository_from_git_config


def _zip_payload(payload: dict[str, object]) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        bundle.writestr("architecture-quality-gate.json", json.dumps(payload))
    return buffer.getvalue()


def test_repository_from_git_config_https(tmp_path: Path) -> None:
    git = tmp_path / ".git"; git.mkdir()
    (git / "config").write_text('[remote "origin"]\n    url = https://github.com/julcapp/DevHub.git\n', encoding="utf-8")
    assert repository_from_git_config(tmp_path) == "julcapp/DevHub"


def test_repository_from_git_config_ssh(tmp_path: Path) -> None:
    git = tmp_path / ".git"; git.mkdir()
    (git / "config").write_text('[remote "origin"]\n    url = git@github.com:julcapp/DevHub.git\n', encoding="utf-8")
    assert repository_from_git_config(tmp_path) == "julcapp/DevHub"


def test_download_quality_gate_history(tmp_path: Path) -> None:
    client = GitHubCIArtifactClient(token="test")
    archive = _zip_payload({"schema_version": 1, "health_score": 88, "quality_gate": "PASS"})
    def fake_request(url: str) -> bytes:
        if "workflows/tests.yml/runs" in url:
            return json.dumps({"workflow_runs": [{"id": 123, "head_sha": "abcdef"}]}).encode()
        if "/runs/123/artifacts" in url:
            return json.dumps({"artifacts": [{"archive_download_url": "https://example/archive.zip"}]}).encode()
        if url == "https://example/archive.zip":
            return archive
        raise AssertionError(url)
    client._request = fake_request  # type: ignore[method-assign]
    count = client.download_quality_gate_history("julcapp/DevHub", tmp_path)
    assert count == 1
    payload = json.loads((tmp_path / "123.json").read_text(encoding="utf-8"))
    assert payload["run_id"] == "123"
    assert payload["commit_sha"] == "abcdef"
