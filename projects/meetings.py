import os
import re
from urllib.parse import parse_qs, unquote, urlparse

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView

from rag_engine.config import RagConfig
from rag_engine.llm import get_llm
from utils.response_utils import CivilErrorResponse, CivilResponse


def parse_meeting_url(raw_url):
    url = str(raw_url or "").strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if parsed.scheme != "https":
        raise ValueError("Use a valid HTTPS meeting URL.")
    if host in {"meet.google.com", "www.meet.google.com"}:
        meeting_id = parsed.path.strip("/").split("/")[0]
        if not re.fullmatch(r"[a-z]{3}-[a-z]{4}-[a-z]{3}", meeting_id):
            raise ValueError("Invalid Google Meet URL.")
        return "google_meet", meeting_id
    if host.endswith("zoom.us"):
        match = re.search(r"/(?:j|wc)/(\d+)", parsed.path)
        if not match:
            raise ValueError("Invalid Zoom meeting URL.")
        return "zoom", match.group(1)
    if host.endswith("teams.microsoft.com") or host.endswith("teams.live.com"):
        query = parse_qs(parsed.query)
        meeting_id = query.get("meetingId", [None])[0] or unquote(parsed.path.strip("/").split("/")[-1])
        if not meeting_id:
            raise ValueError("Invalid Microsoft Teams URL.")
        return "teams", meeting_id
    raise ValueError("Only Google Meet, Zoom and Microsoft Teams links are supported.")


def vexa_request(method, path, **kwargs):
    api_key = os.getenv("VEXA_API_KEY")
    base_url = os.getenv("VEXA_API_URL", "https://api.cloud.vexa.ai").rstrip("/")
    if not api_key:
        raise RuntimeError("VEXA_API_KEY is not configured.")
    headers = kwargs.pop("headers", {})
    headers.update({"X-API-Key": api_key, "Content-Type": "application/json"})
    response = requests.request(method, f"{base_url}{path}", headers=headers, timeout=30, **kwargs)
    response.raise_for_status()
    return response.json()


class MeetingBotStartView(APIView):
    def post(self, request):
        try:
            platform, meeting_id = parse_meeting_url(request.data.get("meeting_url"))
            result = vexa_request("POST", "/bots", json={
                "platform": platform,
                "native_meeting_id": meeting_id,
                "bot_name": os.getenv("VEXA_BOT_NAME", "CivilAI Notetaker"),
            })
        except ValueError as exc:
            return CivilErrorResponse({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return CivilErrorResponse({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.RequestException as exc:
            code = getattr(exc.response, "status_code", 502)
            detail = ""
            if getattr(exc, "response", None) is not None:
                try:
                    payload = exc.response.json()
                    detail = str(payload.get("detail") or payload.get("message") or payload.get("error") or "")
                except (ValueError, AttributeError):
                    detail = ""
            message = detail[:300] or "Vexa rejected the bot request. Check the meeting state and remaining credits."
            return CivilErrorResponse({"error": message}, status=code if 400 <= code < 600 else 502)
        return CivilResponse({"platform": platform, "meeting_id": meeting_id, "provider": result}, status=201, is_success="Meeting assistant started")


class MeetingMomView(APIView):
    def get(self, request):
        platform = request.query_params.get("platform", "")
        meeting_id = request.query_params.get("meeting_id", "")
        if platform not in {"google_meet", "zoom", "teams"} or not meeting_id:
            return CivilErrorResponse({"error": "Valid platform and meeting_id are required."}, status=400)
        try:
            transcript = vexa_request("GET", f"/transcripts/{platform}/{meeting_id}")
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return CivilResponse({"status": "waiting", "segments": 0}, status=200, is_success="Transcript not ready")
            return CivilErrorResponse({"error": "Could not retrieve the Vexa transcript."}, status=502)
        except (requests.RequestException, RuntimeError) as exc:
            return CivilErrorResponse({"error": str(exc)}, status=502)

        segments = [segment for segment in transcript.get("segments", []) if segment.get("completed", True)]
        meeting_status = transcript.get("status", "in_progress")
        if meeting_status != "completed" or not segments:
            return CivilResponse({"status": meeting_status, "segments": len(segments)}, status=200, is_success="Meeting in progress")

        lines = [f"{item.get('speaker') or 'Speaker'}: {item.get('text', '').strip()}" for item in segments if item.get("text", "").strip()]
        transcript_text = "\n".join(lines)
        prompt = (
            "Create professional Minutes of Meeting from the transcript below. Use these headings: "
            "Meeting Summary, Participants, Key Discussion Points, Decisions, Action Items (owner and deadline), "
            "and Follow-ups. Do not invent missing details.\n\nTranscript:\n" + transcript_text[:50000]
        )
        llm = get_llm(RagConfig())
        try:
            mom = llm.generate(prompt, "You create accurate, concise construction-project meeting minutes from transcripts only.")
        except Exception:
            mom = "# Minutes of Meeting\n\n## Transcript\n\n" + transcript_text
        return CivilResponse({"status": "completed", "segments": len(segments), "mom": mom}, status=200, is_success="MOM generated")
