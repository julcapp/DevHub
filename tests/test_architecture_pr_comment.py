from app.workspaces.architecture.pr_comment import COMMENT_MARKER, build_comment, find_existing_comment


def test_build_comment_adds_stable_marker() -> None:
    body = build_comment("# Report\n\nPASS")
    assert body.startswith(COMMENT_MARKER)
    assert "# Report" in body


def test_find_existing_comment_returns_marker_comment_id() -> None:
    comments = [
        {"id": 10, "body": "regular comment"},
        {"id": 22, "body": f"{COMMENT_MARKER}\nold report"},
    ]
    assert find_existing_comment(comments) == 22


def test_find_existing_comment_returns_none_without_marker() -> None:
    assert find_existing_comment([{"id": 1, "body": "other"}]) is None
