"""Microphone recording service. Optional dependency, no network or uploads."""
from __future__ import annotations

from pathlib import Path
import tempfile
import wave


class MicrophoneRecorder:
    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        self._stream = None
        self._frames: list[bytes] = []
        self._capture_error: str | None = None
        self._max_frames = sample_rate * 120

    @property
    def recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        if self.recording:
            raise RuntimeError("Запись уже выполняется")
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("Не установлен модуль sounddevice") from exc
        self._frames = []
        self._capture_error = None

        def on_audio(indata, frames, time_info, status):
            if status:
                self._capture_error = str(status)
            if sum(len(chunk) for chunk in self._frames) + indata.nbytes > self._max_frames * 2:
                self._capture_error = "Превышен лимит записи 120 секунд"
                raise sd.CallbackStop
            self._frames.append(indata.copy().tobytes())

        stream = sd.InputStream(samplerate=self.sample_rate, channels=1,
                                dtype="int16", callback=on_audio)
        try:
            stream.start()
        except Exception:
            stream.close()
            raise
        self._stream = stream

    def stop(self) -> Path:
        if not self.recording:
            raise RuntimeError("Запись не запущена")
        stream = self._stream
        self._stream = None
        stream.stop()
        stream.close()
        if self._capture_error:
            self._frames = []
            raise RuntimeError(f"Ошибка записи: {self._capture_error}")
        if not self._frames:
            raise RuntimeError("Микрофон не записал звук")
        handle = tempfile.NamedTemporaryFile(prefix="devhub-voice-", suffix=".wav",
                                             delete=False)
        path = Path(handle.name)
        try:
            with handle:
                with wave.open(handle, "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(self.sample_rate)
                    wav.writeframes(b"".join(self._frames))
        except Exception:
            path.unlink(missing_ok=True)
            raise
        finally:
            self._frames = []
        return path

    def cancel(self) -> None:
        if self._stream is not None:
            stream = self._stream
            self._stream = None
            stream.stop()
            stream.close()
        self._frames = []
