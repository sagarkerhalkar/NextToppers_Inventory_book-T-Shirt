from __future__ import annotations

from django.conf import settings


class InternalNullOriginCompatibilityMiddleware:
    """Normalize literal ``Origin: null`` only for explicitly approved app hosts.

    Some managed-browser/security configurations replace the browser Origin
    header with the literal string ``null``. Django correctly rejects that
    before form logic runs. For this application, normalize it only when the
    request Host itself is one of Django's explicitly approved hosts.

    This does not disable CSRF. Django's CsrfViewMiddleware still validates the
    authenticated session and the submitted CSRF token after normalization.
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _approved_host(request_host: str) -> bool:
        raw_host = (request_host or "").strip().lower().rstrip(".")
        if not raw_host:
            return False

        # Host headers may include a port. The application currently uses IPv4,
        # localhost and a DNS hostname, so stripping one trailing port is safe.
        hostname = raw_host.rsplit(":", 1)[0] if raw_host.count(":") == 1 else raw_host

        allowed = {
            str(value).strip().lower().rstrip(".")
            for value in settings.ALLOWED_HOSTS
            if value and value != "*" and not str(value).startswith(".")
        }
        return raw_host in allowed or hostname in allowed

    def __call__(self, request):
        if request.method not in self.SAFE_METHODS and request.META.get("HTTP_ORIGIN") == "null":
            host = request.get_host().lower()
            if self._approved_host(host):
                scheme = "https" if request.is_secure() else "http"
                request.META["HTTP_ORIGIN"] = f"{scheme}://{host}"
                request.META["NEXT_TOPPERS_ORIGINAL_ORIGIN"] = "null"

        return self.get_response(request)
