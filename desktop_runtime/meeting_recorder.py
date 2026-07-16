"""Background local meeting recording sessions."""
from __future__ import annotations

import threading
from dataclasses import dataclass

from desktop_runtime.audio_capture import AudioCaptureError, default_recorder
from desktop_runtime.transcription import FasterWhisperTranscriber, TranscriptionError, WhisperCppTranscriber


@dataclass
class RecordingSession:
    meeting_id: int
    stop_event: threading.Event
    thread: threading.Thread


_sessions: dict[int, RecordingSession] = {}
_lock = threading.Lock()


def start_recording_session(meeting_id: int, stt_model_path: str | None = None) -> None:
    with _lock:
        if meeting_id in _sessions:
            return
        stop_event = threading.Event()
        thread = threading.Thread(
            target=_recording_worker,
            args=(meeting_id, stop_event, stt_model_path),
            name=f"civilai-meeting-recorder-{meeting_id}",
            daemon=True,
        )
        _sessions[meeting_id] = RecordingSession(meeting_id, stop_event, thread)
        thread.start()


def stop_recording_session(meeting_id: int, timeout: float = 10.0) -> None:
    with _lock:
        session = _sessions.pop(meeting_id, None)
    if not session:
        return
    session.stop_event.set()
    session.thread.join(timeout=timeout)


def is_recording_session_active(meeting_id: int) -> bool:
    with _lock:
        session = _sessions.get(meeting_id)
        return bool(session and session.thread.is_alive())


def _recording_worker(meeting_id: int, stop_event: threading.Event, stt_model_path: str | None) -> None:
    from django.utils import timezone

    from projects.local_meetings import SegmentInput, append_segments
    from projects.models import Meeting

    com_initialized = False
    if __import__('platform').system().lower() == 'windows':
        try:
            import ctypes
            com_initialized = ctypes.windll.ole32.CoInitialize(None) in (0, 1)
        except Exception:
            com_initialized = False

    recorder = default_recorder()
    transcriber = _transcriber_for_model(stt_model_path) if stt_model_path else None
    try:
        recorder.start()
        while not stop_event.is_set():
            chunk = recorder.read_chunk()
            if not transcriber:
                continue
            try:
                segments = transcriber.transcribe_chunk(chunk)
            except TranscriptionError as exc:
                _mark_failed(meeting_id, str(exc))
                break
            if not segments:
                continue
            meeting = Meeting.objects.get(pk=meeting_id)
            append_segments(
                meeting,
                [
                    SegmentInput(
                        start_seconds=segment.start_seconds,
                        end_seconds=segment.end_seconds,
                        text=segment.text,
                        is_final=True,
                    )
                    for segment in segments
                ],
            )
            if meeting.status == "recording":
                meeting.status = "transcribing"
                meeting.updated_at = timezone.now()
                meeting.save(update_fields=["status", "updated_at"])
    except (AudioCaptureError, Meeting.DoesNotExist) as exc:
        _mark_failed(meeting_id, str(exc))
    except Exception as exc:
        _mark_failed(meeting_id, str(exc))
    finally:
        try:
            recorder.stop()
        except Exception:
            pass
        if com_initialized:
            try:
                import ctypes
                ctypes.windll.ole32.CoUninitialize()
            except Exception:
                pass
        with _lock:
            _sessions.pop(meeting_id, None)


def _mark_failed(meeting_id: int, message: str) -> None:
    from django.utils import timezone

    from projects.models import Meeting

    Meeting.objects.filter(pk=meeting_id).update(
        status="failed",
        error_message=message,
        updated_at=timezone.now(),
    )


def _transcriber_for_model(model_path: str):
    if model_path.lower().endswith(".bin"):
        return WhisperCppTranscriber(model_path)
    return FasterWhisperTranscriber(model_path)
