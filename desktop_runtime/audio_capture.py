"""Platform abstraction for live system-audio capture.

Native implementations are intentionally isolated behind this interface so the
meeting workflow, storage, and UI do not depend on WASAPI, ScreenCaptureKit, or
PipeWire details.
"""
from __future__ import annotations

import platform
import time
from dataclasses import dataclass


class AudioCaptureError(RuntimeError):
    pass


@dataclass(frozen=True)
class AudioChunk:
    pcm: bytes
    sample_rate: int
    channels: int
    start_seconds: float
    end_seconds: float


class SystemAudioRecorder:
    backend_name = "base"

    def __init__(self, sample_rate: int = 16000, chunk_seconds: float = 5.0):
        self.sample_rate = sample_rate
        self.chunk_seconds = chunk_seconds
        self._started_at = 0.0
        self._chunk_index = 0

    def start(self) -> None:
        raise NotImplementedError

    def read_chunk(self) -> AudioChunk:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class SoundcardRecorder(SystemAudioRecorder):
    backend_name = "soundcard"

    def start(self) -> None:
        try:
            import soundcard as sc
        except ImportError as exc:
            raise AudioCaptureError("soundcard is not installed in this build.") from exc

        microphone = self._select_microphone(sc)
        if microphone is None:
            raise AudioCaptureError(self._missing_device_message())

        self._recorder = microphone.recorder(samplerate=self.sample_rate, channels=1)
        self._recorder.__enter__()
        self._started_at = time.monotonic()
        self._chunk_index = 0

    def read_chunk(self) -> AudioChunk:
        if not getattr(self, "_recorder", None):
            raise AudioCaptureError("Recorder has not been started.")

        frames = max(1, int(self.sample_rate * self.chunk_seconds))
        data = self._recorder.record(numframes=frames)
        pcm = _float32_to_pcm16(data)
        start = self._chunk_index * self.chunk_seconds
        self._chunk_index += 1
        return AudioChunk(
            pcm=pcm,
            sample_rate=self.sample_rate,
            channels=1,
            start_seconds=start,
            end_seconds=start + self.chunk_seconds,
        )

    def stop(self) -> None:
        recorder = getattr(self, "_recorder", None)
        if recorder is not None:
            recorder.__exit__(None, None, None)
            self._recorder = None

    def _select_microphone(self, sc):
        system = platform.system().lower()
        if system == "windows":
            speaker = sc.default_speaker()
            return sc.get_microphone(speaker.name, include_loopback=True)
        if system == "linux":
            speaker = sc.default_speaker()
            return sc.get_microphone(speaker.name, include_loopback=True)
        if system == "darwin":
            names = ("blackhole", "loopback", "soundflower")
            for mic in sc.all_microphones(include_loopback=True):
                if any(name in mic.name.lower() for name in names):
                    return mic
            return None
        return None

    def _missing_device_message(self) -> str:
        system = platform.system().lower()
        if system == "darwin":
            return "No macOS virtual system-audio device found. Install/enable BlackHole or another loopback device."
        return "No system-audio loopback source was found."


class WasapiLoopbackRecorder(SoundcardRecorder):
    backend_name = "windows-wasapi-loopback"


class ScreenCaptureKitRecorder(SoundcardRecorder):
    backend_name = "macos-virtual-loopback"


class PipeWireRecorder(SoundcardRecorder):
    backend_name = "linux-pipewire-pulseaudio-monitor"


def default_recorder() -> SystemAudioRecorder:
    system = platform.system().lower()
    if system == "windows":
        return WasapiLoopbackRecorder()
    if system == "darwin":
        return ScreenCaptureKitRecorder()
    if system == "linux":
        return PipeWireRecorder()
    raise AudioCaptureError(f"Unsupported audio capture platform: {platform.system()}")


def available_audio_backend() -> dict:
    recorder = default_recorder()
    ready = False
    message = "Audio capture backend is available."
    try:
        import soundcard as sc

        if platform.system().lower() == "darwin":
            names = ("blackhole", "loopback", "soundflower")
            ready = any(
                any(name in mic.name.lower() for name in names)
                for mic in sc.all_microphones(include_loopback=True)
            )
            if not ready:
                message = "Mac system audio needs a loopback input such as BlackHole. Select it in Audio MIDI Setup after installation."
        else:
            speaker = sc.default_speaker()
            sc.get_microphone(speaker.name, include_loopback=True)
            ready = True
    except Exception as exc:
        message = str(exc)
    return {
        "platform": platform.system(),
        "backend": recorder.backend_name,
        "ready": ready,
        "message": message,
    }


def _float32_to_pcm16(data) -> bytes:
    import numpy as np

    mono = np.asarray(data, dtype=np.float32)
    if mono.ndim > 1:
        mono = mono[:, 0]
    mono = np.clip(mono, -1.0, 1.0)
    return (mono * 32767.0).astype("<i2").tobytes()
