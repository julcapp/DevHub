import json
from io import BytesIO

import pytest

from app.workspaces.stars.github_client import GitHubStarsClient, GitHubStarsError


class Response(BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


def test_client_uses_public_stars_without_token(monkeypatch):
    monkeypatch.delenv("DEVHUB_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    seen = []
    def fake_urlopen(request, **kwargs):
        seen.append(request.full_url)
        return Response(b"[]")
    monkeypatch.setattr("app.workspaces.stars.github_client.urlopen", fake_urlopen)
    assert GitHubStarsClient().fetch_all() == []
    assert "/users/julcapp/starred?" in seen[0]


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
