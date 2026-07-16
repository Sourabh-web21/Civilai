"""Local speech-to-text abstraction."""
from __future__ import annotations

from dataclasses import dataclass
import math
import os
import tempfile
import wave


class TranscriptionError(RuntimeError):
    pass


@dataclass(frozen=True)
class TranscribedSegment:
    start_seconds: float
    end_seconds: float
    text: str


class LocalTranscriber:
    backend_name = "base"

    def transcribe_chunk(self, audio_chunk) -> list[TranscribedSegment]:
        raise NotImplementedError


class FasterWhisperTranscriber(LocalTranscriber):
    backend_name = "faster-whisper"

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise TranscriptionError("faster-whisper is not installed.") from exc
            self._model = WhisperModel(self.model_path, device="cpu", compute_type="int8")

    def transcribe_chunk(self, audio_chunk) -> list[TranscribedSegment]:
        self._ensure_model()
        if _is_silent(audio_chunk.pcm):
            return []

        wav_path = None
        try:
            fd, wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            with wave.open(wav_path, "wb") as wav:
                wav.setnchannels(audio_chunk.channels)
                wav.setsampwidth(2)
                wav.setframerate(audio_chunk.sample_rate)
                wav.writeframes(audio_chunk.pcm)

            segments, _info = self._model.transcribe(
                wav_path,
                vad_filter=True,
                word_timestamps=False,
                condition_on_previous_text=False,
            )
            return [
                TranscribedSegment(
                    start_seconds=audio_chunk.start_seconds + float(segment.start),
                    end_seconds=audio_chunk.start_seconds + float(segment.end),
                    text=segment.text.strip(),
                )
                for segment in segments
                if segment.text and segment.text.strip()
            ]
        finally:
            if wav_path:
                try:
                    os.remove(wav_path)
                except OSError:
                    pass


class WhisperCppTranscriber(LocalTranscriber):
    backend_name = "whisper.cpp"

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                from pywhispercpp.model import Model
            except ImportError as exc:
                raise TranscriptionError("pywhispercpp is not installed.") from exc
            self._model = Model(self.model_path, redirect_whispercpp_logs_to=False)

    def transcribe_chunk(self, audio_chunk) -> list[TranscribedSegment]:
        self._ensure_model()
        if _is_silent(audio_chunk.pcm):
            return []

        wav_path = None
        try:
            fd, wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            with wave.open(wav_path, "wb") as wav:
                wav.setnchannels(audio_chunk.channels)
                wav.setsampwidth(2)
                wav.setframerate(audio_chunk.sample_rate)
                wav.writeframes(audio_chunk.pcm)

            segments = self._model.transcribe(wav_path, no_context=True, print_progress=False)
            output = []
            for segment in segments:
                text = getattr(segment, "text", "")
                if not text or not text.strip():
                    continue
                start = _segment_seconds(segment, "t0", "start")
                end = _segment_seconds(segment, "t1", "end")
                output.append(
                    TranscribedSegment(
                        start_seconds=audio_chunk.start_seconds + start,
                        end_seconds=audio_chunk.start_seconds + end,
                        text=text.strip(),
                    )
                )
            return output
        finally:
            if wav_path:
                try:
                    os.remove(wav_path)
                except OSError:
                    pass


def _is_silent(pcm: bytes, threshold: float = 0.004) -> bool:
    if not pcm:
        return True
    sample_count = len(pcm) // 2
    if sample_count == 0:
        return True
    total = 0
    for index in range(0, len(pcm) - 1, 2):
        sample = int.from_bytes(pcm[index : index + 2], "little", signed=True)
        total += sample * sample
    rms = math.sqrt(total / sample_count) / 32768.0
    return rms < threshold


def _segment_seconds(segment, centisecond_attr: str, seconds_attr: str) -> float:
    if hasattr(segment, seconds_attr):
        value = getattr(segment, seconds_attr)
        if isinstance(value, (int, float)):
            return float(value)
    if hasattr(segment, centisecond_attr):
        value = getattr(segment, centisecond_attr)
        if isinstance(value, (int, float)):
            return float(value) / 100.0
    return 0.0
