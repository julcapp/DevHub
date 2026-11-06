"""Offline speech recognition engine; dependencies loaded only when used.

Model directory must be pre-provisioned by the Windows installer. No implicit
model download is permitted, so transcription remains private and offline.
"""
from __future__ import annotations

from pathlib import Path
import os
import sys


class OfflineSpeechRecognizer:
    def __init__(self, model_dir: Path) -> None:
        self.model_dir = Path(model_dir)

    def validate(self) -> None:
        if not self.model_dir.is_dir():
            raise FileNotFoundError(f"Локальная модель распознавания не найдена: {self.model_dir}")
        if not (self.model_dir / "model.bin").is_file():
            raise FileNotFoundError(f"Файл model.bin отсутствует: {self.model_dir}")

    def transcribe_file(self, audio_path: Path, language: str = "ru") -> str:
        self.validate()
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Аудиозапись не найдена: {audio_path}")
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("Установите локальные зависимости из requirements-voice.txt") from exc
        # Local directory only: do not resolve remote model names.
        model = WhisperModel(str(self.model_dir), device="cpu", compute_type="int8",
                             local_files_only=True)
        segments, _ = model.transcribe(str(audio_path), language=language, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments if segment.text.strip())


def default_model_dir() -> Path:
    """Shared packaged model location, overridable for developer testing."""
    configured = os.environ.get("DEVHUB_WHISPER_MODEL")
    if configured:
        return Path(configured)
    # PyInstaller one-directory bundles place data under sys._MEIPASS.
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root is not None:
        return Path(bundle_root) / "models" / "whisper"
    return Path(__file__).resolve().parents[3] / "models" / "whisper"
