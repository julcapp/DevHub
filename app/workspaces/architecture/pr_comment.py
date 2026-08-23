from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path

COMMENT_MARKER = "<!-- devhub-architecture-quality-gate -->"


def build_comment(report_markdown: str) -> str:
    return f"{COMMENT_MARKER}\n{report_markdown.strip()}\n"


def find_existing_comment(comments: list[dict[str, object]]) -> int | None:
    for comment in comments:
        body = str(comment.get("body", ""))
        if COMMENT_MARKER in body:
            value = comment.get("id")
            return int(value) if value is not None else None
    return None


def _request(url: str, token: str, method: str = "GET", payload: dict[str, object] | None = None) -> object:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DevHub-Architecture-Quality-Gate",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read().decode("utf-8")
        return json.loads(content) if content else {}


def publish_pr_comment(repo: str, pr_number: int, token: str, report_path: Path) -> str:
    body = build_comment(report_path.read_text(encoding="utf-8"))
    api = f"https://api.github.com/repos/{repo}"
    comments = _request(f"{api}/issues/{pr_number}/comments?per_page=100", token)
    if not isinstance(comments, list):
        raise RuntimeError("GitHub API returned an unexpected comments payload")
    existing = find_existing_comment(comments)
    if existing is not None:
        _request(f"{api}/issues/comments/{existing}", token, "PATCH", {"body": body})
        return "updated"
    _request(f"{api}/issues/{pr_number}/comments", token, "POST", {"body": body})
    return "created"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish DevHub Architecture Quality Gate report to a pull request")
    parser.add_argument("report", type=Path)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--pr", type=int, default=int(os.environ["GITHUB_PR_NUMBER"]) if os.environ.get("GITHUB_PR_NUMBER") else None)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    args = parser.parse_args(argv)
    if not args.repo or not args.pr or not args.token:
        parser.error("repo, PR number and token are required")
    action = publish_pr_comment(args.repo, args.pr, args.token, args.report)
    print(f"Architecture PR comment {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
