from rest_framework.views import APIView
from rest_framework import status
from rest_framework.throttling import SimpleRateThrottle
import imaplib, email, json, os, re
from email.header import decode_header
from datetime import datetime, timedelta, timezone
from utils.response_utils import CivilResponse, CivilErrorResponse
from django.conf import settings
from django.core.cache import cache

MEETING_URL_RE = re.compile(
    r"https://(?:meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}|(?:[\w.-]+\.)?zoom\.us/(?:j|wc)/\d+(?:\?[^\s<>\"]+)?|teams\.(?:microsoft|live)\.com/[^\s<>\"]+)",
    re.IGNORECASE,
)


class EmailExtractionThrottle(SimpleRateThrottle):
    """Protect the manual sync endpoint from repeated mailbox polling."""

    scope = "email_extract"

    def get_rate(self):
        return settings.EMAIL_IMAP_API_RATE

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = f"user-{request.user.pk}"
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}

def decode_mime_words(s):
    decoded_fragments = decode_header(s)
    return ''.join([
        fragment.decode(enc or 'utf-8', errors='ignore') if isinstance(fragment, bytes) else fragment
        for fragment, enc in decoded_fragments
    ])

class EmailExtractorView(APIView):
    throttle_classes = [EmailExtractionThrottle]

    def post(self, request):
        email_account = settings.EMAIL_HOST_USER
        email_password = settings.EMAIL_HOST_PASSWORD
        if not email_account or not email_password:
            return CivilErrorResponse(
                {"error": "Email is not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        cooldown_key = f"email-extract-cooldown:{email_account.lower()}"
        if not cache.add(cooldown_key, True, timeout=settings.EMAIL_IMAP_COOLDOWN_SECONDS):
            return CivilErrorResponse(
                {"error": f"Email was checked recently. Try again in {settings.EMAIL_IMAP_COOLDOWN_SECONDS} seconds."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        SAVE_FOLDER = os.path.join(settings.MEDIA_ROOT, "emails_backup")
        PROCESSED_LOG = os.path.join(SAVE_FOLDER, "processed_ids.txt")
        MEETINGS_LOG = os.path.join(SAVE_FOLDER, "detected_meetings.json")
        os.makedirs(SAVE_FOLDER, exist_ok=True)

        processed_ids = set()
        if os.path.exists(PROCESSED_LOG):
            with open(PROCESSED_LOG, "r") as f:
                processed_ids = set(line.strip() for line in f)

        extracted = []
        recent_emails = []
        try:
            with open(MEETINGS_LOG, "r", encoding="utf-8") as f:
                detected_meetings = json.load(f)
        except (OSError, ValueError):
            detected_meetings = []

        now = datetime.now(timezone.utc)
        for item in detected_meetings:
            try:
                detected_at = datetime.fromisoformat(str(item.get("detected_at", "")).replace("Z", "+00:00"))
                item["expired"] = now - detected_at > timedelta(hours=24)
            except (TypeError, ValueError):
                item["expired"] = True

        mail = None
        skipped_large_attachments = 0
        try:
            mail = imaplib.IMAP4_SSL(
                settings.EMAIL_IMAP_HOST,
                settings.EMAIL_IMAP_PORT,
                timeout=30,
            )
            mail.login(email_account, email_password)
            mail.select("inbox")

            date_since = (datetime.now() - timedelta(days=settings.EMAIL_IMAP_LOOKBACK_DAYS)).strftime("%d-%b-%Y")
            status_, email_ids = mail.search(None, f'(SINCE "{date_since}")')
            if status_ != "OK":
                raise RuntimeError("Mailbox search failed")

            # Process only the newest bounded batch. BODY.PEEK keeps unread mail unread.
            email_ids = email_ids[0].split()[-settings.EMAIL_IMAP_MAX_MESSAGES:]

            for email_id in email_ids:
                fetch_status, msg_data = mail.fetch(email_id, "(BODY.PEEK[])")
                if fetch_status != "OK":
                    continue

                for part in msg_data:
                    if not isinstance(part, tuple):
                        continue

                    msg = email.message_from_bytes(part[1])
                    msg_id = msg.get("Message-ID", "").strip()
                    recent_emails.append({
                        "message_id": msg_id,
                        "sender": decode_mime_words(msg.get("From", "")),
                        "subject": decode_mime_words(msg.get("Subject", "")) or "No subject",
                        "date": msg.get("Date", ""),
                        "attachments": [],
                    })
                    # Meeting detection runs even for previously processed mail,
                    # so upgrading AiConnect does not require resending invites.
                    raw_message = part[1].decode("utf-8", errors="ignore")
                    existing_urls = {item.get("url") for item in detected_meetings}
                    for meeting_url in MEETING_URL_RE.findall(raw_message):
                        clean_url = meeting_url.rstrip(".,);]")
                        if clean_url not in existing_urls:
                            detected_meetings.append({
                                "url": clean_url,
                                "subject": decode_mime_words(msg.get("Subject", "")),
                                "sender": decode_mime_words(msg.get("From", "")),
                                "detected_at": now.isoformat(),
                                "expired": False,
                            })
                            existing_urls.add(clean_url)
                    if not msg_id or msg_id in processed_ids:
                        continue

                    raw_subject = msg.get("Subject", "")
                    subject = decode_mime_words(raw_subject)
                    description = ""
                    attachments = []

                    for body_part in msg.walk():
                        content_disposition = body_part.get("Content-Disposition", "").lower()
                        content_type = body_part.get_content_type()

                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            try:
                                description = body_part.get_payload(decode=True).decode(body_part.get_content_charset() or 'utf-8', errors='ignore').strip()
                            except:
                                description = ""

                        if "attachment" in content_disposition:
                            filename = body_part.get_filename()
                            if filename:
                                filename = decode_mime_words(filename)
                                safe_filename = "".join(c if c.isalnum() or c in '._-' else '_' for c in filename)
                                attachment_path = os.path.join(SAVE_FOLDER, safe_filename)

                                base, ext = os.path.splitext(attachment_path)
                                counter = 1
                                while os.path.exists(attachment_path):
                                    attachment_path = f"{base}_{counter}{ext}"
                                    counter += 1

                                payload = body_part.get_payload(decode=True) or b""
                                max_bytes = settings.EMAIL_IMAP_MAX_ATTACHMENT_MB * 1024 * 1024
                                if len(payload) > max_bytes:
                                    skipped_large_attachments += 1
                                    continue

                                with open(attachment_path, "wb") as f:
                                    f.write(payload)

                                # Convert to media-relative URL
                                relative_url = os.path.relpath(attachment_path, settings.MEDIA_ROOT)
                                file_url = f"{settings.MEDIA_URL}{relative_url}".replace('\\', '/')  # for Windows
                                attachments.append(file_url)

                    with open(PROCESSED_LOG, "a") as f:
                        f.write(f"{msg_id}\n")

                    extracted.append({
                        "message_id": msg_id,
                        "sender": decode_mime_words(msg.get("From", "")),
                        "subject": subject,
                        "description": description,
                        "attachments": attachments
                    })
                    if recent_emails and recent_emails[-1].get("message_id") == msg_id:
                        recent_emails[-1]["attachments"] = attachments
                    existing_urls = {item.get("url") for item in detected_meetings if not item.get("expired")}
                    for meeting_url in MEETING_URL_RE.findall(description):
                        clean_url = meeting_url.rstrip(".,);]")
                        if clean_url not in existing_urls:
                            detected_meetings.append({"url": clean_url, "subject": subject, "sender": decode_mime_words(msg.get("From", "")), "detected_at": now.isoformat(), "expired": False})
                            existing_urls.add(clean_url)

        except imaplib.IMAP4.error:
            cache.delete(cooldown_key)
            return CivilErrorResponse(
                {"error": "Mailbox authentication failed. Check the email address and app password in .env."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except (OSError, RuntimeError):
            cache.delete(cooldown_key)
            return CivilErrorResponse(
                {"error": "The mailbox could not be reached or read. Please try again later."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        finally:
            if mail is not None:
                try:
                    mail.logout()
                except (imaplib.IMAP4.error, OSError):
                    pass

        # New saved attachments must invalidate the singleton RAG index.
        if any(item["attachments"] for item in extracted):
            from rag_engine.service import reset
            reset()

        try:
            with open(MEETINGS_LOG, "w", encoding="utf-8") as f:
                json.dump(detected_meetings[-50:], f, ensure_ascii=False, indent=2)
        except OSError:
            pass

        return CivilResponse(
            {
                "emails_extracted": extracted,
                "recent_emails": recent_emails[-5:][::-1],
                "email_account": email_account,
                "messages_checked": len(email_ids),
                "message_limit": settings.EMAIL_IMAP_MAX_MESSAGES,
                "skipped_large_attachments": skipped_large_attachments,
                "rag_reload_queued": any(item["attachments"] for item in extracted),
                "detected_meetings": detected_meetings[-20:],
            },
            status=status.HTTP_200_OK,
            is_success="Email extracted successfully"
        )
