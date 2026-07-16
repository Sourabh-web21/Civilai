"""Local meeting transcript and MOM processing.

This module is the offline replacement path for the cloud meeting-bot flow. It
does not capture audio yet; it provides the persistence and deterministic
summarization primitives that live transcription will feed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from django.utils import timezone

from desktop_runtime.app_paths import exports_dir

from .models import Meeting, MeetingExport, MeetingSummary, TranscriptSegment


@dataclass(frozen=True)
class SegmentInput:
    start_seconds: float
    end_seconds: float
    text: str
    is_final: bool = True


def create_meeting(title: str = "", user=None, audio_source: str = "") -> Meeting:
    return Meeting.objects.create(
        title=title.strip(),
        status="created",
        created_by=user if getattr(user, "is_authenticated", False) else None,
        audio_source=audio_source.strip(),
    )


def mark_recording_started(meeting: Meeting) -> Meeting:
    meeting.status = "recording"
    meeting.started_at = timezone.now()
    meeting.save(update_fields=["status", "started_at", "updated_at"])
    return meeting


def mark_recording_stopped(meeting: Meeting) -> Meeting:
    meeting.status = "summarizing"
    meeting.stopped_at = timezone.now()
    if meeting.started_at:
        meeting.duration_seconds = max(0.0, (meeting.stopped_at - meeting.started_at).total_seconds())
    meeting.save(update_fields=["status", "stopped_at", "duration_seconds", "updated_at"])
    return meeting


def append_segments(meeting: Meeting, segments: Iterable[SegmentInput]) -> list[TranscriptSegment]:
    existing = meeting.segments.order_by("-sequence").values_list("sequence", flat=True).first()
    next_sequence = 1 if existing is None else existing + 1
    rows = []
    for offset, segment in enumerate(segments):
        text = " ".join((segment.text or "").split())
        if not text:
            continue
        rows.append(
            TranscriptSegment(
                meeting=meeting,
                sequence=next_sequence + offset,
                start_seconds=max(0.0, float(segment.start_seconds)),
                end_seconds=max(float(segment.start_seconds), float(segment.end_seconds)),
                text=text,
                is_final=segment.is_final,
            )
        )
    return TranscriptSegment.objects.bulk_create(rows)


def build_chunk_summaries(meeting: Meeting, max_segments_per_chunk: int = 12) -> list[MeetingSummary]:
    MeetingSummary.objects.filter(meeting=meeting, summary_type="chunk").delete()
    segments = list(meeting.segments.filter(is_final=True).order_by("sequence"))
    summaries = []
    for chunk_index, start in enumerate(range(0, len(segments), max_segments_per_chunk), start=1):
        chunk = segments[start:start + max_segments_per_chunk]
        if not chunk:
            continue
        summaries.append(
            MeetingSummary.objects.create(
                meeting=meeting,
                summary_type="chunk",
                chunk_index=chunk_index,
                start_seconds=chunk[0].start_seconds,
                end_seconds=chunk[-1].end_seconds,
                source_segment_start=chunk[0].sequence,
                source_segment_end=chunk[-1].sequence,
                summary_markdown=_extractive_chunk_summary(chunk),
            )
        )
    return summaries


def build_final_mom(meeting: Meeting) -> str:
    chunks = list(meeting.summaries.filter(summary_type="chunk").order_by("chunk_index"))
    if not chunks:
        chunks = build_chunk_summaries(meeting)

    discussion = "\n".join(summary.summary_markdown for summary in chunks if summary.summary_markdown.strip())
    mom = (
        "# Minutes of Meeting\n\n"
        "## Meeting Overview\n\n"
        f"- Duration: {_duration_label(meeting.duration_seconds)}\n"
        f"- Transcript segments: {meeting.segments.filter(is_final=True).count()}\n\n"
        "## Executive Summary\n\n"
        f"{_first_non_empty_line(discussion) or 'No confirmed transcript content was captured.'}\n\n"
        "## Key Discussion Points\n\n"
        f"{discussion or '- No key discussion points captured.'}\n\n"
        "## Decisions Made\n\n"
        f"{_extract_lines(discussion, ('decided', 'decision', 'approved', 'agreed')) or '- No explicit decisions captured.'}\n\n"
        "## Action Items\n\n"
        f"{_extract_lines(discussion, ('action', 'follow up', 'todo', 'assign', 'complete')) or '- No explicit action items captured.'}\n\n"
        "## Open Questions\n\n"
        f"{_extract_lines(discussion, ('?', 'question', 'clarify', 'pending')) or '- No explicit open questions captured.'}\n\n"
        "## Final Summary\n\n"
        f"{_compact_text(discussion, max_items=5) or 'No final summary available.'}\n"
    )
    meeting.status = "completed"
    meeting.final_mom = mom
    meeting.save(update_fields=["status", "final_mom", "updated_at"])
    MeetingSummary.objects.update_or_create(
        meeting=meeting,
        summary_type="final",
        defaults={"summary_markdown": mom},
    )
    return mom


def export_mom(meeting: Meeting, export_format: str) -> MeetingExport:
    export_format = export_format.lower().strip()
    if export_format not in {"markdown", "txt", "docx", "pdf"}:
        raise ValueError("Unsupported export format.")
    mom = meeting.final_mom or build_final_mom(meeting)
    folder = exports_dir() / f"meeting-{meeting.pk}"
    folder.mkdir(parents=True, exist_ok=True)
    suffix = "md" if export_format == "markdown" else export_format
    path = folder / f"minutes-of-meeting.{suffix}"
    if export_format == "docx":
        _write_docx(path, mom)
    elif export_format == "pdf":
        _write_simple_pdf(path, mom)
    else:
        path.write_text(mom, encoding="utf-8")
    return MeetingExport.objects.create(meeting=meeting, export_format=export_format, file_path=str(path))


def _extractive_chunk_summary(segments: list[TranscriptSegment]) -> str:
    lines = []
    for segment in segments:
        text = _compact_sentence(segment.text)
        if text:
            lines.append(f"- [{_timestamp(segment.start_seconds)}-{_timestamp(segment.end_seconds)}] {text}")
    return "\n".join(lines)


def _timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _duration_label(seconds: float | None) -> str:
    if seconds is None:
        return "Unknown"
    return _timestamp(seconds)


def _compact_sentence(text: str, max_words: int = 36) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(".,;:") + "."


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip().lstrip("-").strip()
        if cleaned:
            return cleaned
    return ""


def _extract_lines(text: str, keywords: tuple[str, ...]) -> str:
    matches = []
    for line in text.splitlines():
        lower = line.lower()
        if any(keyword in lower for keyword in keywords):
            matches.append(line)
    return "\n".join(matches)


def _compact_text(text: str, max_items: int = 5) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:max_items])


def _write_docx(path: Path, markdown: str) -> None:
    paragraphs = [line.strip() for line in markdown.splitlines()]
    document_xml = "".join(
        f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>"
        for line in paragraphs
    )
    with ZipFile(path, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>'
        ))
        docx.writestr("_rels/.rels", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/>'
            '</Relationships>'
        ))
        docx.writestr("word/document.xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body>{document_xml}</w:body></w:document>"
        ))


def _write_simple_pdf(path: Path, text: str) -> None:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()[:92]
        if line:
            lines.append(line)
        if len(lines) >= 42:
            break
    if not lines:
        lines = ["Minutes of Meeting"]
    content = ["BT", "/F1 10 Tf", "50 790 Td"]
    for index, line in enumerate(lines):
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index:
            content.append("0 -16 Td")
        content.append(f"({safe}) Tj")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"5 0 obj << /Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj\n",
    ]
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(data))
        data.extend(obj)
    xref = len(data)
    data.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(bytes(data))
