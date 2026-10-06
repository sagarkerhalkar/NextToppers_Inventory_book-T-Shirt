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


def request(host, port, method, path, *, headers=None, body=None, timeout=90.0):
    connection = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        request_headers = {
            "Host": f"{host}:{port}",
            "User-Agent": "NextToppersInventoryIisLoginVerifier/4.0",
            "Connection": "close",
        }
        request_headers.update(headers or {})
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        content = response.read(8 * 1024 * 1024)
        return response.status, response.reason, response.getheaders(), content
    finally:
        connection.close()


def cookies_from(headers):
    cookies = {}
    for name, value in headers:
        if name.lower() != "set-cookie":
            continue
        parsed = SimpleCookie()
        parsed.load(value)
        for key, morsel in parsed.items():
            if morsel.value:
                cookies[key] = morsel.value
    return cookies


def cookie_header(cookies):
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def hidden_value(html: bytes, field_name: str) -> str:
    pattern = rb'name="' + re.escape(field_name.encode("ascii")) + rb'" value="([^"]+)"'
    match = re.search(pattern, html)
    require(match is not None, f"Missing hidden field: {field_name}")
    return match.group(1).decode("ascii")


def verify_nonce_login(host: str, port: int, timeout: float) -> None:
    origin = f"http://{host}:{port}"
    status, reason, headers, html = request(host, port, "GET", "/login/?fresh=nonce-v3", timeout=timeout)
    print(f"GET {origin}/login/?fresh=nonce-v3 -> HTTP {status} {reason}", flush=True)
    require(status == 200, f"Login GET returned HTTP {status}")
    require(b'name="login_nonce"' in html, "Login nonce was not rendered")
    require(b'name="csrfmiddlewaretoken"' not in html, "Login still uses the failed CSRF-cookie flow")

    cookies = cookies_from(headers)
    require(settings.SESSION_COOKIE_NAME in cookies, f"Missing session cookie {settings.SESSION_COOKIE_NAME}")
    nonce = hidden_value(html, "login_nonce")
    body = urlencode({
        "username": "__INVALID_NONCE_PROBE__",
        "password": "invalid-password",
        "login_nonce": nonce,
    }).encode("ascii")

    status, reason, _, html = request(
        host,
        port,
        "POST",
        "/login/",
        body=body,
        timeout=timeout,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(body)),
            "Cookie": cookie_header(cookies),
            "Origin": origin,
            "Referer": f"{origin}/login/?fresh=nonce-v3",
        },
    )
    print(f"POST {origin}/login/ with one-time nonce -> HTTP {status} {reason}", flush=True)
    require(status == 200, f"Nonce login POST returned HTTP {status}")
    require(b'name="login_nonce"' in html, "Invalid-password page did not rotate the nonce")
    require(b"Security verification failed" not in html, "Login returned a security-verification failure")
    require(
        b"Please enter a correct employee id and password" in html
        or b"Login User ID or password is incorrect." in html,
        "Login POST did not reach the authentication form",
    )
    print("LIVE_NONCE_LOGIN_POST_OK", flush=True)


def choose_admin() -> User:
    roles = [User.Role.SUPER_ADMIN, User.Role.ADMIN]
    preferred = User.objects.filter(
        employee_id="NXTTP0036",
        is_active=True,
        must_change_password=False,
        role__in=roles,
    ).first()
    if preferred:
        return preferred
    user = User.objects.filter(is_active=True, must_change_password=False, role=User.Role.SUPER_ADMIN).first()
    if user:
        return user
    user = User.objects.filter(is_active=True, must_change_password=False, role=User.Role.ADMIN).first()
    if user:
        return user
    raise RuntimeError("No active Admin/Super Admin is available for live verification")


def verify_authenticated_application(host: str, port: int, timeout: float) -> None:
    origin = f"http://{host}:{port}"
    user = choose_admin()
    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.set_expiry(300)
    session.save()
    require(session.session_key, "Temporary authenticated session was not created")

    try:
        cookies = {settings.SESSION_COOKIE_NAME: session.session_key}
        for path in ("/", "/books/", "/employees/", "/tshirts/stock/", "/reports/", "/reports/audit-evidence/"):
            status, reason, response_headers, content = request(
                host, port, "GET", path, timeout=timeout, headers={"Cookie": cookie_header(cookies)}
            )
            print(f"AUTH GET {origin}{path} -> HTTP {status} {reason}", flush=True)
            require(status == 200, f"Authenticated page {path} returned HTTP {status}")
            require(b"Login User ID" not in content, f"{path} redirected to login")
            require(b"Security verification failed" not in content, f"Security failure appeared on {path}")
            require(b"Server Error" not in content, f"Server error appeared on {path}")
            cookies.update(cookies_from(response_headers))

        status, reason, response_headers, content = request(
            host,
            port,
            "GET",
            "/health/session-csrf-token/",
            timeout=timeout,
            headers={"Cookie": cookie_header(cookies)},
        )
        print(f"AUTH GET {origin}/health/session-csrf-token/ -> HTTP {status} {reason}", flush=True)
        require(status == 200, f"Session-CSRF token endpoint returned HTTP {status}")
        cookies.update(cookies_from(response_headers))
        token = json.loads(content.decode("utf-8"))["csrfToken"]

        status, reason, _, content = request(
            host,
            port,
            "POST",
            "/health/session-csrf-probe/",
            body=b"",
            timeout=timeout,
            headers={
                "Cookie": cookie_header(cookies),
                "Origin": origin,
                "Referer": f"{origin}/",
                "X-CSRFToken": token,
                "Content-Length": "0",
            },
        )
        print(f"AUTH POST {origin}/health/session-csrf-probe/ -> HTTP {status} {reason}", flush=True)
        require(status == 200, f"Authenticated session-CSRF POST returned HTTP {status}")
        require(content == b"SESSION_CSRF_OK", "Session-CSRF response marker was incorrect")
        print(f"LIVE_AUTHENTICATED_CORE_PAGES_AND_CSRF_OK using {user.employee_id}", flush=True)
    finally:
        if session.session_key:
            session.delete(session.session_key)
            print("Temporary authenticated verification session removed.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("host", nargs="?", default="156.156.40.51")
    parser.add_argument("port", nargs="?", type=int, default=3458)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()
    verify_nonce_login(args.host, args.port, args.timeout)
    verify_authenticated_application(args.host, args.port, args.timeout)
    print("IIS_NONCE_LOGIN_AND_APPLICATION_LOGIC_VERIFIED", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"IIS_NONCE_LOGIN_AND_APPLICATION_LOGIC_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
