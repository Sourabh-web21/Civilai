from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from desktop_runtime.audio_capture import available_audio_backend
from desktop_runtime.meeting_recorder import (
    is_recording_session_active,
    start_recording_session,
    stop_recording_session,
)
from utils.response_utils import CivilErrorResponse, CivilResponse

from .local_meetings import (
    SegmentInput,
    append_segments,
    build_chunk_summaries,
    build_final_mom,
    create_meeting,
    export_mom,
    mark_recording_started,
    mark_recording_stopped,
)
from .models import Meeting, OfflineModelSetting
from .serializers import (
    AppendSegmentsSerializer,
    LocalMeetingStartSerializer,
    MeetingExportRequestSerializer,
    MeetingExportSerializer,
    MeetingSerializer,
    TranscriptSegmentSerializer,
)


def meeting_queryset():
    return Meeting.objects.annotate(
        segment_count=Count("segments", distinct=True),
        summary_count=Count("summaries", distinct=True),
    )


class LocalMeetingStartView(APIView):
    def post(self, request):
        serializer = LocalMeetingStartSerializer(data=request.data)
        if not serializer.is_valid():
            return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        meeting = create_meeting(
            title=serializer.validated_data.get("title", ""),
            user=request.user,
            audio_source=serializer.validated_data.get("audio_source", "system"),
        )
        mark_recording_started(meeting)
        stt_model = _selected_model_path("stt")
        if stt_model:
            meeting.stt_model_id = stt_model["model_id"]
            meeting.save(update_fields=["stt_model_id", "updated_at"])
        try:
            start_recording_session(meeting.id, stt_model_path=stt_model["model_path"] if stt_model else None)
        except Exception as exc:
            meeting.status = "failed"
            meeting.error_message = str(exc)
            meeting.save(update_fields=["status", "error_message", "updated_at"])
        payload = MeetingSerializer(meeting_queryset().get(pk=meeting.pk)).data
        return CivilResponse(payload, status=status.HTTP_201_CREATED, is_success="Local meeting started")


class LocalMeetingBackendStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return CivilResponse(
            {"audio": available_audio_backend()},
            status=status.HTTP_200_OK,
            is_success="Local meeting backend status",
        )


class LocalMeetingDetailView(APIView):
    def get(self, request, meeting_id):
        meeting = get_object_or_404(meeting_queryset(), pk=meeting_id)
        payload = MeetingSerializer(meeting).data
        payload["segments"] = TranscriptSegmentSerializer(
            meeting.segments.order_by("sequence")[:200],
            many=True,
        ).data
        return CivilResponse(payload, status=status.HTTP_200_OK, is_success="Local meeting retrieved")


class LocalMeetingStatusView(APIView):
    def get(self, request, meeting_id):
        meeting = get_object_or_404(meeting_queryset(), pk=meeting_id)
        segment_count = meeting.segments.count()
        summary_count = meeting.summaries.count()
        progress = _progress_for_status(meeting.status)
        return CivilResponse(
            {
                "id": meeting.id,
                "status": meeting.status,
                "progress": progress,
                "segments": segment_count,
                "summaries": summary_count,
                "has_mom": bool(meeting.final_mom),
                "recorder_active": is_recording_session_active(meeting.id),
                "message": _status_message(meeting.status),
                "error_message": meeting.error_message,
            },
            status=status.HTTP_200_OK,
            is_success="Local meeting status",
        )


class LocalMeetingAppendSegmentsView(APIView):
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        if meeting.status in {"completed", "failed", "cancelled"}:
            return CivilErrorResponse(
                {"error": "Cannot append transcript segments to a finished meeting."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = AppendSegmentsSerializer(data=request.data)
        if not serializer.is_valid():
            return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        created = append_segments(
            meeting,
            [
                SegmentInput(
                    start_seconds=item["start_seconds"],
                    end_seconds=item["end_seconds"],
                    text=item["text"],
                    is_final=item.get("is_final", True),
                )
                for item in serializer.validated_data["segments"]
            ],
        )
        if meeting.status == "recording":
            meeting.status = "transcribing"
            meeting.save(update_fields=["status", "updated_at"])

        return CivilResponse(
            {
                "meeting_id": meeting.id,
                "created": TranscriptSegmentSerializer(created, many=True).data,
                "segment_count": meeting.segments.count(),
            },
            status=status.HTTP_201_CREATED,
            is_success="Transcript segments appended",
        )


class LocalMeetingStopView(APIView):
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        if meeting.status in {"completed", "failed", "cancelled"}:
            return CivilErrorResponse(
                {"error": "Meeting is already finished."},
                status=status.HTTP_409_CONFLICT,
            )
        stop_recording_session(meeting.id)
        mark_recording_stopped(meeting)
        summaries = build_chunk_summaries(meeting)
        mom = build_final_mom(meeting)
        return CivilResponse(
            {
                "meeting": MeetingSerializer(meeting_queryset().get(pk=meeting.pk)).data,
                "chunk_summaries": len(summaries),
                "mom": mom,
            },
            status=status.HTTP_200_OK,
            is_success="Local meeting stopped and MOM generated",
        )


class LocalMeetingMomView(APIView):
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        summaries = build_chunk_summaries(meeting)
        mom = build_final_mom(meeting)
        return CivilResponse(
            {"meeting_id": meeting.id, "chunk_summaries": len(summaries), "mom": mom},
            status=status.HTTP_200_OK,
            is_success="Local MOM generated",
        )


class LocalMeetingExportView(APIView):
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        serializer = MeetingExportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            export = export_mom(meeting, serializer.validated_data["export_format"])
        except ValueError as exc:
            return CivilErrorResponse({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return CivilResponse(
            MeetingExportSerializer(export).data,
            status=status.HTTP_201_CREATED,
            is_success="Meeting exported",
        )


def _progress_for_status(meeting_status):
    return {
        "created": 5,
        "recording": 20,
        "transcribing": 45,
        "summarizing": 70,
        "building_mom": 85,
        "completed": 100,
        "failed": 100,
        "cancelled": 100,
    }.get(meeting_status, 0)


def _status_message(meeting_status):
    return {
        "created": "Ready",
        "recording": "Recording...",
        "transcribing": "Transcribing...",
        "summarizing": "Generating Summary...",
        "building_mom": "Building MOM...",
        "completed": "Completed",
        "failed": "Failed",
        "cancelled": "Cancelled",
    }.get(meeting_status, meeting_status)


def _selected_model_path(kind):
    setting = (
        OfflineModelSetting.objects.filter(kind=kind, is_downloaded=True)
        .exclude(model_path="")
        .first()
    )
    if not setting:
        return None
    return {"model_id": setting.model_id, "model_path": setting.model_path}
