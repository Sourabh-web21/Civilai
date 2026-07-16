import time

from django.conf import settings
from django.core.management.base import BaseCommand

from projects.extract import EmailExtractorView


class Command(BaseCommand):
    help = "Continuously synchronize the configured IMAP inbox for AiConnect."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run one synchronization and exit.")
        parser.add_argument("--interval", type=int, help="Seconds between checks (minimum 60).")

    def handle(self, *args, **options):
        interval = max(60, options["interval"] or settings.EMAIL_IMAP_SYNC_INTERVAL_SECONDS)
        while True:
            response = EmailExtractorView().post(None)
            ok = getattr(response, "status_code", 500) < 400
            self.stdout.write(
                self.style.SUCCESS("Email synchronization completed.")
                if ok else self.style.WARNING(f"Email synchronization skipped or failed ({response.status_code}).")
            )
            if options["once"]:
                return
            time.sleep(interval)
