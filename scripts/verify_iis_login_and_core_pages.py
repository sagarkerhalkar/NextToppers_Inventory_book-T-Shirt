from __future__ import annotations

import argparse
import http.client
import os
import re
import sys
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlencode

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
os.chdir(APP_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nexttoppers_inventory.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth import (  # noqa: E402
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
)
from django.contrib.sessions.backends.db import SessionStore  # noqa: E402

from inventory.models import User  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def request(
    host: str,
    port: int,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: float = 90.0,
) -> tuple[int, str, list[tuple[str, str]], bytes]:
    connection = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        request_headers = {
            "Host": f"{host}:{port}",
            "User-Agent": "NextToppersInventoryIisLoginVerifier/1.0",
            "Connection": "close",
        }
        request_headers.update(headers or {})
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        content = response.read(8 * 1024 * 1024)
        return response.status, response.reason, response.getheaders(), content
    finally:
        connection.close()


def cookies_from(headers: list[tuple[str, str]]) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for name, value in headers:
        if name.lower() != "set-cookie":
            continue
        parsed = SimpleCookie()
        parsed.load(value)
        for key, morsel in parsed.items():
            cookies[key] = morsel.value
    return cookies


def csrf_token_from(html: bytes) -> str:
    match = re.search(rb'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    if not match:
        raise RuntimeError("The login page did not contain a CSRF form token.")
    return match.group(1).decode("ascii")


def cookie_header(values: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in values.items())


def verify_csrf_login_post(host: str, port: int, timeout: float) -> None:
    origin = f"http://{host}:{port}"
    login_path = "/login/?next=/"

    status, reason, headers, login_html = request(
        host,
        port,
        "GET",
        login_path,
        timeout=timeout,
    )
    print(f"GET {origin}{login_path} -> HTTP {status} {reason}", flush=True)
    require(status == 200, f"Login GET returned HTTP {status}")
    require(b"csrfmiddlewaretoken" in login_html, "Login GET did not render a CSRF token")

    cookies = cookies_from(headers)
    require(
        settings.CSRF_COOKIE_NAME in cookies,
        f"Login GET did not set the expected CSRF cookie {settings.CSRF_COOKIE_NAME}",
    )
    token = csrf_token_from(login_html)

    post_body = urlencode(
        {
            "username": "__INVALID_CSRF_PROBE__",
            "password": "invalid-password",
            "csrfmiddlewaretoken": token,
        }
    ).encode("ascii")

    status, reason, _, post_html = request(
        host,
        port,
        "POST",
        login_path,
        body=post_body,
        timeout=timeout,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(post_body)),
            "Cookie": cookie_header(cookies),
            "Origin": origin,
            "Referer": f"{origin}{login_path}",
        },
    )
    print(f"POST {origin}{login_path} with CSRF cookie/token -> HTTP {status} {reason}", flush=True)
    require(status == 200, f"CSRF-protected login POST returned HTTP {status}")
    require(
        b"Login User ID or password is incorrect." in post_html,
        "Login POST was not accepted by CSRF and processed by Django LoginView",
    )
    require(b"CSRF verification failed" not in post_html, "Login POST returned a CSRF failure page")
    print("LIVE_CSRF_LOGIN_POST_OK", flush=True)


def choose_test_user() -> User:
    admin_roles = [User.Role.SUPER_ADMIN, User.Role.ADMIN]
    preferred = User.objects.filter(
        employee_id="NXTTP0036",
        is_active=True,
        must_change_password=False,
        role__in=admin_roles,
    ).first()
    if preferred:
        return preferred

    user = User.objects.filter(
        is_active=True,
        must_change_password=False,
        role=User.Role.SUPER_ADMIN,
    ).first()
    if user:
        return user

    user = User.objects.filter(
        is_active=True,
        must_change_password=False,
        role=User.Role.ADMIN,
    ).first()
    if user:
        return user

    raise RuntimeError("No active Admin/Super Admin with a completed password was available for the temporary session check.")


def create_temporary_authenticated_session(user: User) -> SessionStore:
    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.set_expiry(300)
    session.save()
    return session


def verify_authenticated_core_pages(host: str, port: int, timeout: float) -> None:
    user = choose_test_user()
    session = create_temporary_authenticated_session(user)
    require(session.session_key, "Temporary authenticated session key was not created")

    try:
        cookie = f"{settings.SESSION_COOKIE_NAME}={session.session_key}"
        paths = (
            "/",
            "/books/",
            "/employees/",
            "/tshirts/stock/",
            "/reports/",
            "/reports/audit-evidence/",
        )

        for path in paths:
            status, reason, _, content = request(
                host,
                port,
                "GET",
                path,
                timeout=timeout,
                headers={"Cookie": cookie},
            )
            print(f"AUTH GET http://{host}:{port}{path} -> HTTP {status} {reason}", flush=True)
            require(status == 200, f"Authenticated core page {path} returned HTTP {status}")
            require(b"csrfmiddlewaretoken" not in content or b"GLOBAL INVENTORY COMMAND CENTER" in content or path != "/", "Dashboard redirected to the login form")
            require(b"Login User ID" not in content, f"Authenticated core page {path} redirected to login")
            require(b"CSRF verification failed" not in content, f"CSRF failure content appeared on {path}")
            require(b"Forbidden (403)" not in content, f"Forbidden content appeared on {path}")
            require(b"Server Error" not in content, f"Server error content appeared on {path}")

        print(f"LIVE_AUTHENTICATED_CORE_PAGES_OK using {user.employee_id}", flush=True)
    finally:
        if session.session_key:
            session.delete(session.session_key)
            print("Temporary authenticated verification session removed.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify IIS login CSRF POST and authenticated core application pages without knowing a password."
    )
    parser.add_argument("host", nargs="?", default="156.156.40.51")
    parser.add_argument("port", nargs="?", type=int, default=3458)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    verify_csrf_login_post(args.host, args.port, args.timeout)
    verify_authenticated_core_pages(args.host, args.port, args.timeout)
    print("IIS_LOGIN_AND_APPLICATION_LOGIC_VERIFIED", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"IIS_LOGIN_AND_APPLICATION_LOGIC_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
