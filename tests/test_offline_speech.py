from pathlib import Path

import pytest

from app.workspaces.notebook.offline_speech import OfflineSpeechRecognizer, default_model_dir


def test_offline_recognizer_requires_packaged_model(tmp_path):
    recognizer = OfflineSpeechRecognizer(tmp_path / "missing")
    with pytest.raises(FileNotFoundError, match="модель"):
        recognizer.validate()


def test_offline_recognizer_requires_model_binary(tmp_path):
    model_dir = tmp_path / "whisper"
    model_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="model.bin"):
        OfflineSpeechRecognizer(model_dir).validate()


def test_offline_recognizer_requires_audio_file(tmp_path):
    model_dir = tmp_path / "whisper"
    model_dir.mkdir()
    (model_dir / "model.bin").write_bytes(b"test")
    with pytest.raises(FileNotFoundError, match="Аудиозапись"):
        OfflineSpeechRecognizer(model_dir).transcribe_file(tmp_path / "missing.wav")


def test_model_path_override(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVHUB_WHISPER_MODEL", str(tmp_path))
    assert default_model_dir() == tmp_path


def test_model_path_from_pyinstaller_bundle(tmp_path, monkeypatch):
    import sys
    monkeypatch.delenv("DEVHUB_WHISPER_MODEL", raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert default_model_dir() == tmp_path / "models" / "whisper"
