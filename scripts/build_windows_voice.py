"""Build a Windows x64 offline DevHub distribution with an embedded Whisper model.

Run on Windows in a clean build environment. No downloads occur at runtime.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import platform
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def validate_model(path: Path) -> None:
    required = ("model.bin", "config.json", "tokenizer.json")
    missing = [name for name in required if not (path / name).is_file()]
    if missing:
        raise SystemExit("Whisper model incomplete: " + ", ".join(missing))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True,
                        help="Existing local CTranslate2 multilingual Whisper model directory")
    parser.add_argument("--entry", type=Path, default=ROOT / "run.py")
    args = parser.parse_args()
    if platform.system() != "Windows" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise SystemExit("Build must run on Windows x64")
    model_dir = args.model_dir.resolve()
    validate_model(model_dir)
    if not args.entry.is_file():
        raise SystemExit(f"Application entry point not found: {args.entry}")
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onedir", "--windowed",
        "--name", "DevHub",
        "--collect-all", "faster_whisper",
        "--collect-all", "ctranslate2",
        "--collect-all", "sounddevice",
        "--add-data", f"{model_dir};models/whisper",
        str(args.entry),
    ], cwd=ROOT, check=True)
    print("Bundle created under dist/DevHub; installer and Windows smoke tests still required.")


if __name__ == "__main__":
    main()
