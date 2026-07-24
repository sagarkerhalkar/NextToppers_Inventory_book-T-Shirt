from __future__ import annotations

import os
import sys
from html.parser import HTMLParser
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


class StylesheetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        values = {name.lower(): value or "" for name, value in attrs}
        if "stylesheet" in values.get("rel", "").lower() and values.get("href"):
            self.stylesheets.append(values["href"])


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def bootstrap_stylesheet_from(html: bytes) -> str:
    parser = StylesheetParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    for href in parser.stylesheets:
        if href.startswith("/static/vendor/bootstrap/bootstrap.min") and href.endswith(".css"):
            return href
    raise RuntimeError(
        "Login page does not reference a local Bootstrap stylesheet. "
        f"Stylesheets returned: {parser.stylesheets}"
    )


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
    bootstrap_href = bootstrap_stylesheet_from(login.content)
    print(f"Local Bootstrap stylesheet: {bootstrap_href}")

    print("RUNTIME_PREFLIGHT_OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RUNTIME_PREFLIGHT_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
