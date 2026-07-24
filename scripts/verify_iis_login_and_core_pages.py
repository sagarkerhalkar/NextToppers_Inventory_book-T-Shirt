from __future__ import annotations

import argparse
import http.client
import json
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
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY  # noqa: E402
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
            "User-Agent": "NextToppersInventoryIisLoginVerifier/3.0",
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
            if morsel.value:
                cookies[key] = morsel.value
    return cookies


def cookie_header(values: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in values.items())


def hidden_value(html: bytes, field_name: str) -> str:
    pattern = rb'name="' + re.escape(field_name.encode("ascii")) + rb'" value="([^"]+)"'
    match = re.search(pattern, html)
    if not match:
        raise RuntimeError(f"The page did not contain hidden field {field_name}.")
    return match.group(1).decode("ascii")


def verify_nonce_login_post(host: str, port: int, timeout: float) -> None:
    origin = f"http://{host}:{port}"
    login_path = "/login/?fresh=1"

    status, reason, headers, login_html = request(host, port, "GET", login_path, timeout=timeout)
    print(f"GET {origin}{login_path} -> HTTP {status} {reason}", flush=True)
    require(status == 200, f"Login GET returned HTTP {status}")
    require(b'name="login_nonce"' in login_html, "Login GET did not render the one-time nonce")
    require(b'name="csrfmiddlewaretoken"' not in login_html, "Login still depends on the failing CSRF cookie")

    cookies = cookies_from(headers)
    require(
        settings.SESSION_COOKIE_NAME in cookies,
        f"Login GET did not set pre-authentication session cookie {settings.SESSION_COOKIE_NAME}",
    )
    nonce = hidden_value(login_html, "login_nonce")

    post_body = urlencode(
        {
            "username": "__INVALID_NONCE_PROBE__",
            "password": "invalid-password",
            "login_nonce": nonce,
        }
    ).encode("ascii")

    status, reason, response_headers, post_html = request(
        host,
        port,
        "POST",
        "/login/",
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
    print(f"POST {origin}/login/ with one-time nonce -> HTTP {status} {reason}", flush=True)
    require(status == 200, f"Nonce-protected login POST returned HTTP {status}")
    require(b"Login User ID or password is incorrect." in post_html, "Login POST did not reach Django LoginView")
    require(b"Security verification failed" not in post_html, "Login POST returned a security failure")
    require(b'name="login_nonce"' in post_html, "Invalid-password response did not rotate the login nonce")

    refreshed = cookies_from(response_headers)
    if settings.SESSION_COOKIE_NAME in refreshed:
        cookies[settings.SESSION_COOKIE_NAME] = refreshed[settings.SESSION_COOKIE_NAME]

    print("LIVE_NONCE_LOGIN_POST_OK", flush=True)


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

    raise RuntimeError("No active Admin/Super Admin is available for authenticated verification.")


def create_temporary_authenticated_session(user: User) -> SessionStore:
    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.set_expiry(300)
    session.save()
    return session


def verify_authenticated_core_pages_and_csrf(host: str, port: int, timeout: float) -> None:
    origin = f"http://{host}:{port}"
    user = choose_test_user()
    session = create_temporary_authenticated_session(user)
    require(session.session_key, "Temporary authenticated session key was not created")

    try:
        cookies = {settings.SESSION_COOKIE_NAME: session.session_key}
        paths = (
            "/",
            "/books/",
            "/employees/",
            "/tshirts/stock/",
            "/reports/",
            "/reports/audit-evidence/",
        )

        for path in paths:
            status, reason, response_headers, content = request(
                host,
                port,
                "GET",
                path,
                timeout=timeout,
                headers={"Cookie": cookie_header(cookies)},
            )
            print(f"AUTH GET {origin}{path} -> HTTP {status} {reason}", flush=True)
            require(status == 200, f"Authenticated core page {path} returned HTTP {status}")
            require(b"Login User ID" not in content, f"Authenticated core page {path} redirected to login")
            require(b"Security verification failed" not in content, f"Security failure content appeared on {path}")
            require(b"Forbidden (403)" not in content, f"Forbidden content appeared on {path}")
            require(b"Server Error" not in content, f"Server error content appeared on {path}")
            updated = cookies_from(response_headers)
            if settings.SESSION_COOKIE_NAME in updated:
                cookies[settings.SESSION_COOKIE_NAME] = updated[settings.SESSION_COOKIE_NAME]

        status, reason, response_headers, token_body = request(
            host,
            port,
            "GET",
            "/health/session-csrf-token/",
            timeout=timeout,
            headers={"Cookie": cookie_header(cookies)},
        )
        print(f"AUTH GET {origin}/health/session-csrf-token/ -> HTTP {status} {reason}", flush=True)
        require(status == 200, f"Session CSRF token endpoint returned HTTP {status}")
        token = json.loads(token_body.decode("utf-8"))["csrfToken"]
        updated = cookies_from(response_headers)
        if settings.SESSION_COOKIE_NAME in updated:
            cookies[settings.SESSION_COOKIE_NAME] = updated[settings.SESSION_COOKIE_NAME]

        status, reason, _, probe_body = request(
            host,
            port,
            "POST",
            "/health/session-csrf-probe/",
            timeout=timeout,
            headers={
                "Cookie": cookie_header(cookies),
                "Origin": origin,
                "Referer": f"{origin}/",
                "X-CSRFToken": token,
                "Content-Length": "0",
            },
            body=b"",
        )
        print(f"AUTH POST {origin}/health/session-csrf-probe/ -> HTTP {status} {reason}", flush=True)
        require(status == 200, f"Authenticated session-CSRF POST returned HTTP {status}")
        require(probe_body == b"SESSION_CSRF_OK", "Session-CSRF probe marker was incorrect")

        print(f"LIVE_AUTHENTICATED_CORE_PAGES_AND_CSRF_OK using {user.employee_id}", flush=True)
    finally:
        if session.session_key:
            session.delete(session.session_key)
            print("Temporary authenticated verification session removed.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify nonce login, authenticated core pages and session-backed CSRF through IIS."
    )
    parser.add_argument("host", nargs="?", default="156.156.40.51")
    parser.add_argument("port", nargs="?", type=int, default=3458)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    verify_nonce_login_post(args.host, args.port, args.timeout)
    verify_authenticated_core_pages_and_csrf(args.host, args.port, args.timeout)
    print("IIS_NONCE_LOGIN_AND_APPLICATION_LOGIC_VERIFIED", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"IIS_NONCE_LOGIN_AND_APPLICATION_LOGIC_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
