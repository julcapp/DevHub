from __future__ import annotations

import wave

import pytest

from app.workspaces.notebook.microphone import MicrophoneRecorder


def test_recorder_rejects_stop_before_start():
    recorder = MicrophoneRecorder()
    with pytest.raises(RuntimeError, match="не запущена"):
        recorder.stop()


def test_recorder_cancel_without_stream():
    recorder = MicrophoneRecorder()
    recorder.cancel()
    assert not recorder.recording


def test_recorder_writes_valid_wav(tmp_path):
    class FakeStream:
        def stop(self):
            pass
        def close(self):
            pass

    recorder = MicrophoneRecorder()
    recorder._stream = FakeStream()
    recorder._frames = [b"\x00\x00" * 16]
    path = recorder.stop()
    try:
        with wave.open(str(path), "rb") as audio:
            assert audio.getframerate() == 16000
            assert audio.getnchannels() == 1
            assert audio.getnframes() == 16
    finally:
        path.unlink(missing_ok=True)


def test_recorder_rejects_empty_audio():
    class FakeStream:
        def stop(self):
            pass
        def close(self):
            pass

    recorder = MicrophoneRecorder()
    recorder._stream = FakeStream()
    with pytest.raises(RuntimeError, match="не записал звук"):
        recorder.stop()


def test_recorder_rejects_capture_error():
    class FakeStream:
        def stop(self):
            pass
        def close(self):
            pass

    recorder = MicrophoneRecorder()
    recorder._stream = FakeStream()
    recorder._frames = [b"\\x00\\x00"]
    recorder._capture_error = "input overflow"
    with pytest.raises(RuntimeError, match="input overflow"):
        recorder.stop()
    assert not recorder.recording
