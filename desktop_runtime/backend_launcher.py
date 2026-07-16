"""Packaged backend entrypoint for desktop builds."""
from __future__ import annotations

import os
import secrets
import sys


def bootstrap_desktop_database() -> None:
    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)

    from db.models import User

    email = os.getenv("CIVILAI_DESKTOP_ADMIN_EMAIL", "admin@civil.ai")
    password = os.getenv("CIVILAI_DESKTOP_ADMIN_PASSWORD", "admin12345")
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": "admin",
            "full_name": "CivilAI Admin",
            "role": "admin",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )
    changed = False
    if created or not user.has_usable_password():
        user.set_password(password)
        changed = True
    for field, value in {
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
        "role": "admin",
    }.items():
        if getattr(user, field) != value:
            setattr(user, field, value)
            changed = True
    if changed:
        user.save()


def main() -> None:
    os.environ.setdefault("CIVILAI_DESKTOP", "1")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "construction_ai.settings")
    os.environ.setdefault("CIVILAI_DESKTOP_TOKEN", secrets.token_urlsafe(32))
    os.environ["DEBUG"] = os.getenv("DEBUG", "False")
    port = int(os.getenv("CIVILAI_BACKEND_PORT") or "8765")
    bootstrap_desktop_database()
    from django.core.management import execute_from_command_line

    execute_from_command_line([
        sys.argv[0],
        "runserver",
        f"127.0.0.1:{port}",
        "--noreload",
    ])


if __name__ == "__main__":
    main()
