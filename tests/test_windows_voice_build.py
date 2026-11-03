from pathlib import Path

import pytest

from scripts.build_windows_voice import validate_model


def test_model_bundle_requires_all_files(tmp_path):
    (tmp_path / "model.bin").write_bytes(b"placeholder")
    with pytest.raises(SystemExit, match="config.json"):
        validate_model(tmp_path)


def test_model_bundle_accepts_complete_local_directory(tmp_path):
    for name in ("model.bin", "config.json", "tokenizer.json"):
        (tmp_path / name).write_bytes(b"placeholder")
    validate_model(tmp_path)
