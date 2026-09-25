from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CICacheStatus:
    last_updated: str
    records: int
    removed: int
    max_records: int


class CICacheManager:
    META_FILE = "_cache.json"

    def __init__(self, max_records: int = 50) -> None:
        self.max_records = max(1, max_records)

    def _result_files(self, root: Path) -> list[Path]:
        files = [path for path in root.glob("*.json") if path.name != self.META_FILE]
        def key(path: Path) -> tuple[int, str]:
            try:
                return (int(path.stem), path.name)
            except ValueError:
                return (-1, path.name)
        return sorted(files, key=key, reverse=True)

    def maintain(self, root: Path) -> CICacheStatus:
        root.mkdir(parents=True, exist_ok=True)
        files = self._result_files(root)
        stale = files[self.max_records:]
        removed = 0
        for path in stale:
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
        records = len(self._result_files(root))
        status = CICacheStatus(
            last_updated=datetime.now(timezone.utc).isoformat(),
            records=records,
            removed=removed,
            max_records=self.max_records,
        )
        (root / self.META_FILE).write_text(json.dumps(asdict(status), ensure_ascii=False, indent=2), encoding="utf-8")
        return status

    def load_status(self, root: Path) -> CICacheStatus | None:
        path = root / self.META_FILE
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return CICacheStatus(
                last_updated=str(payload["last_updated"]),
                records=int(payload["records"]),
                removed=int(payload.get("removed", 0)),
                max_records=int(payload["max_records"]),
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def clear(self, root: Path) -> int:
        if not root.exists():
            return 0
        removed = 0
        for path in self._result_files(root):
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
        meta = root / self.META_FILE
        try:
            if meta.exists():
                meta.unlink()
        except OSError:
            pass
        return removed
