from __future__ import annotations

import os
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
os.chdir(APP_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nexttoppers_inventory.settings")

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402
from django.db import connection  # noqa: E402
from django.test import Client  # noqa: E402

from inventory.models import BrandingSettings  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    print("1/6 Django system check")
    call_command("check", verbosity=1)

    print("2/6 SQLite connectivity")
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        require(cursor.fetchone() == (1,), "SQLite SELECT 1 did not return the expected result")

    print("3/6 Branding query")
    BrandingSettings.load()

    client = Client()

    print("4/6 Internal health request")
    health = client.get("/health/", HTTP_HOST="127.0.0.1")
    require(health.status_code == 200, f"Health endpoint returned HTTP {health.status_code}")
    require(health.content == b"NEXT_TOPPERS_INVENTORY_OK", "Health marker is incorrect")

    print("5/6 Internal login-page rendering")
    login = client.get("/login/", HTTP_HOST="127.0.0.1")
    require(login.status_code == 200, f"Login page returned HTTP {login.status_code}")
    require(b"Next Toppers" in login.content, "Login page content marker was not found")
    require(b"csrfmiddlewaretoken" in login.content, "Login form CSRF token was not rendered")

    print("6/6 Login page is fully local")
    for forbidden in (b"fonts.googleapis.com", b"fonts.gstatic.com", b"cdn.jsdelivr.net"):
        require(forbidden not in login.content, f"Login page still contains external dependency: {forbidden.decode()}")
    require(
        b"/static/vendor/bootstrap/bootstrap.min.css" in login.content,
        "Login page does not reference the local Bootstrap stylesheet",
    )

    print("RUNTIME_PREFLIGHT_OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RUNTIME_PREFLIGHT_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
