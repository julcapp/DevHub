from pathlib import Path

from app.services.session_service import SessionService, WorkspaceSession


def test_session_round_trip(tmp_path: Path) -> None:
    service = SessionService(tmp_path / "session.json")
    expected = WorkspaceSession(
        geometry="geometry",
        window_state="state",
        selected_repository="C:/Projects/DevHub",
        active_section="research",
        clean_shutdown=True,
    )

    service.save(expected)
    actual = service.load()

    assert actual == expected


def test_mark_startup_marks_session_unclean(tmp_path: Path) -> None:
    service = SessionService(tmp_path / "session.json")
    service.save(WorkspaceSession(clean_shutdown=True))

    session = service.mark_startup()

    assert session.clean_shutdown is False
    assert service.load().clean_shutdown is False


def test_mark_clean_shutdown_persists_flag(tmp_path: Path) -> None:
    service = SessionService(tmp_path / "session.json")
    session = WorkspaceSession(clean_shutdown=False)

    service.mark_clean_shutdown(session)

    assert service.load().clean_shutdown is True
