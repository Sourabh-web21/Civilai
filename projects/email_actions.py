from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from rest_framework import status
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from utils.response_utils import CivilErrorResponse, CivilResponse


class EmailSendThrottle(SimpleRateThrottle):
    scope = "email_send"

    def get_rate(self):
        return getattr(settings, "EMAIL_SEND_API_RATE", "10/hour")

    def get_cache_key(self, request, view):
        ident = f"user-{request.user.pk}" if request.user.is_authenticated else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class EmailActionView(APIView):
    """Send an explicitly confirmed compose/reply/forward action through SMTP."""

    throttle_classes = [EmailSendThrottle]
    valid_actions = {"compose", "reply", "forward"}

    def post(self, request):
        action = str(request.data.get("action", "compose")).strip().lower()
        recipients = request.data.get("to", [])
        subject = str(request.data.get("subject", "")).strip()
        body = str(request.data.get("body", "")).strip()
        original_message_id = str(request.data.get("original_message_id", "")).strip()

        if isinstance(recipients, str):
            recipients = [item.strip() for item in recipients.split(",") if item.strip()]
        if action not in self.valid_actions:
            return CivilErrorResponse({"error": "Action must be compose, reply, or forward."}, status=status.HTTP_400_BAD_REQUEST)
        if not recipients or len(recipients) > 10 or any("@" not in item for item in recipients):
            return CivilErrorResponse({"error": "Provide between 1 and 10 valid recipient email addresses."}, status=status.HTTP_400_BAD_REQUEST)
        if not subject or len(subject) > 200:
            return CivilErrorResponse({"error": "Subject is required and must be at most 200 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if not body or len(body) > 10000:
            return CivilErrorResponse({"error": "Message is required and must be at most 10,000 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            return CivilErrorResponse({"error": "SMTP email is not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        prefix = "Re: " if action == "reply" else "Fwd: " if action == "forward" else ""
        if prefix and not subject.lower().startswith(prefix.lower().strip()):
            subject = f"{prefix}{subject}"

        headers = {}
        if action == "reply" and original_message_id:
            headers = {"In-Reply-To": original_message_id, "References": original_message_id}

        try:
            message = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=settings.EMAIL_HOST_USER,
                to=recipients,
                headers=headers,
            )
            sent = message.send(fail_silently=False)
        except Exception:
            return CivilErrorResponse(
                {"error": "Email could not be sent. Check SMTP credentials and try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return CivilResponse(
            {"sent": bool(sent), "action": action, "recipients": recipients, "subject": subject},
            status=status.HTTP_200_OK,
            is_success="Email sent successfully",
        )
