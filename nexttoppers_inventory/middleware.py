from __future__ import annotations

from django.conf import settings


class InternalNullOriginCompatibilityMiddleware:
    """Normalize Chrome's ``Origin: null`` only for approved internal HTTP hosts.

    Some managed-browser/security configurations replace the real same-origin
    value with the literal string ``null``. Django correctly rejects that value
    before form logic runs. For this internal HTTP-only application, rewrite it
    to the exact request origin only when the Host header is explicitly approved.

    This middleware does not bypass CSRF token validation. Django's normal
    CsrfViewMiddleware still requires the authenticated session and valid token.
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in self.SAFE_METHODS and request.META.get("HTTP_ORIGIN") == "null":
            host = request.get_host().lower()
            allowed_hosts = {
                f"{settings.PUBLIC_INVENTORY_HOST}:{settings.PUBLIC_INVENTORY_PORT}".lower(),
                f"localhost:{settings.PUBLIC_INVENTORY_PORT}",
                f"127.0.0.1:{settings.PUBLIC_INVENTORY_PORT}",
            }
            if host in allowed_hosts:
                request.META["HTTP_ORIGIN"] = f"http://{host}"
                request.META["NEXT_TOPPERS_ORIGINAL_ORIGIN"] = "null"

        return self.get_response(request)
