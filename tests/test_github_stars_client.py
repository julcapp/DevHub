import json
from io import BytesIO

import pytest

from app.workspaces.stars.github_client import GitHubStarsClient, GitHubStarsError


class Response(BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


def test_client_requires_token(monkeypatch):
    monkeypatch.delenv("DEVHUB_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(GitHubStarsError):
        GitHubStarsClient().fetch_all()


def test_client_maps_github_payload(monkeypatch):
    payload = [{
        "full_name": "owner/project",
        "description": "Useful project",
        "html_url": "https://github.com/owner/project",
        "language": "Python",
        "license": {"spdx_id": "MIT"},
    }]
    monkeypatch.setattr(
        "app.workspaces.stars.github_client.urlopen",
        lambda *args, **kwargs: Response(json.dumps(payload).encode()),
    )
    repos = GitHubStarsClient(token="test").fetch_all()
    assert repos[0].full_name == "owner/project"
    assert repos[0].license_name == "MIT"
