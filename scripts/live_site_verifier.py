from __future__ import annotations

import argparse
import http.client
import sys
from html.parser import HTMLParser


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


def fetch(host: str, port: int, path: str, timeout: float) -> tuple[int, str, bytes]:
    connection = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        connection.request(
            "GET",
            path,
            headers={
                "Host": f"{host}:{port}",
                "User-Agent": "NextToppersInventoryLiveVerifier/1.0",
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        body = response.read(4 * 1024 * 1024)
        return response.status, response.reason, body
    finally:
        connection.close()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def find_bootstrap_path(html: bytes) -> str:
    parser = StylesheetParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    for href in parser.stylesheets:
        if href.startswith("/static/vendor/bootstrap/bootstrap.min") and href.endswith(".css"):
            return href
    raise RuntimeError(f"Local Bootstrap stylesheet was not found. Stylesheets returned: {parser.stylesheets}")


def verify(host: str, port: int, timeout: float) -> None:
    base = f"http://{host}:{port}"

    status, reason, health = fetch(host, port, "/health/", timeout)
    print(f"{base}/health/ -> HTTP {status} {reason}")
    require(status == 200, f"Health endpoint returned HTTP {status}")
    require(health == b"NEXT_TOPPERS_INVENTORY_OK", "Health marker was incorrect")

    status, reason, login = fetch(host, port, "/login/", timeout)
    print(f"{base}/login/ -> HTTP {status} {reason}")
    require(status == 200, f"Login page returned HTTP {status}")
    require(b"csrfmiddlewaretoken" in login, "Login CSRF marker was not found")
    require(b"Next Toppers" in login, "Login title marker was not found")
    for forbidden in (b"fonts.googleapis.com", b"fonts.gstatic.com", b"cdn.jsdelivr.net"):
        require(forbidden not in login, f"External dependency remains in login page: {forbidden.decode()}")

    bootstrap_path = find_bootstrap_path(login)
    print(f"Generated Bootstrap URL: {bootstrap_path}")
    status, reason, css = fetch(host, port, bootstrap_path, timeout)
    print(f"{base}{bootstrap_path} -> HTTP {status} {reason}")
    require(status == 200, f"Generated Bootstrap stylesheet returned HTTP {status}")
    require(b"Bootstrap" in css, "Bootstrap content marker was not found")

    print(f"LIVE_SITE_VERIFIED: {base}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify health, login and the exact generated Bootstrap URL.")
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()
    verify(args.host, args.port, args.timeout)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"LIVE_SITE_VERIFICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
