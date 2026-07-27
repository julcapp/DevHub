from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QByteArray


@dataclass(slots=True)
class WorkspaceSession:
    geometry: str = ""
    window_state: str = ""
    selected_repository: str = ""
    active_section: str = "projects"
    clean_shutdown: bool = True


class SessionService:
    """Persist and restore non-sensitive DevHub workspace state."""

    def __init__(self, session_path: Path | None = None) -> None:
        self.session_path = session_path or Path(".devhub") / "session.json"

    def load(self) -> WorkspaceSession:
        if not self.session_path.exists():
            return WorkspaceSession()

        try:
            raw: dict[str, Any] = json.loads(self.session_path.read_text(encoding="utf-8"))
            allowed = WorkspaceSession.__dataclass_fields__.keys()
            return WorkspaceSession(**{key: raw[key] for key in allowed if key in raw})
        except (OSError, ValueError, TypeError):
            return WorkspaceSession(clean_shutdown=False)

    def save(self, session: WorkspaceSession) -> None:
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.session_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(asdict(session), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self.session_path)

    def mark_startup(self) -> WorkspaceSession:
        session = self.load()
        session.clean_shutdown = False
        self.save(session)
        return session

    def mark_clean_shutdown(self, session: WorkspaceSession) -> None:
        session.clean_shutdown = True
        self.save(session)

    @staticmethod
    def encode_qt_state(value: QByteArray) -> str:
        return bytes(value.toBase64()).decode("ascii")

    @staticmethod
    def decode_qt_state(value: str) -> QByteArray:
        return QByteArray.fromBase64(value.encode("ascii")) if value else QByteArray()
