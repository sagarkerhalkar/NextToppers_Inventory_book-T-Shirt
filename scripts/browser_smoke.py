from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from playwright.sync_api import Page, sync_playwright

BASE_URL = os.getenv("BROWSER_SMOKE_BASE_URL", "http://127.0.0.1:8000")
EMPLOYEE_ID = os.getenv("BROWSER_SMOKE_EMPLOYEE_ID", "NXTTP9000")
PASSWORD = os.getenv("BROWSER_SMOKE_PASSWORD", "ReleaseTest1234")


@dataclass(frozen=True)
class Viewport:
    name: str
    width: int
    height: int


VIEWPORTS = (
    Viewport("desktop", 1440, 900),
    Viewport("tablet", 820, 1180),
    Viewport("android", 412, 915),
    Viewport("iphone", 390, 844),
)

PAGES = (
    "/",
    "/books/",
    "/employees/",
    "/tshirts/stock/",
    "/tshirts/allocations/",
    "/reports/",
    "/settings/branding/",
)


def assert_no_horizontal_overflow(page: Page, label: str) -> None:
    overflow = page.evaluate(
        """() => ({
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
            bodyScrollWidth: document.body ? document.body.scrollWidth : 0
        })"""
    )
    if overflow["scrollWidth"] > overflow["clientWidth"] + 4:
        raise AssertionError(f"{label}: horizontal overflow detected: {overflow}")


def login(page: Page) -> None:
    page.goto(f"{BASE_URL}/login/", wait_until="networkidle")
    page.locator('input[name="username"]').fill(EMPLOYEE_ID)
    page.locator('input[name="password"]').fill(PASSWORD)
    page.locator('button[type="submit"]').click()
    page.wait_for_load_state("networkidle")
    if "/login/" in page.url:
        raise AssertionError("Browser smoke login failed")


def run() -> int:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for viewport in VIEWPORTS:
                context = browser.new_context(viewport={"width": viewport.width, "height": viewport.height})
                page = context.new_page()
                login(page)
                for path in PAGES:
                    response = page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
                    if response is None or response.status >= 400:
                        raise AssertionError(f"{viewport.name} {path}: HTTP {response.status if response else 'none'}")
                    assert_no_horizontal_overflow(page, f"{viewport.name} {path}")
                    if not page.locator("body").is_visible():
                        raise AssertionError(f"{viewport.name} {path}: body is not visible")
                context.close()
                print(f"PASS viewport={viewport.name}")
        finally:
            browser.close()
    print("BROWSER_SMOKE_OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        print(f"BROWSER_SMOKE_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
