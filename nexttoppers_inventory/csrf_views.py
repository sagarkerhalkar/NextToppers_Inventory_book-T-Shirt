from __future__ import annotations

import logging

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("django.security.csrf")


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    """Log reverse-proxy details without redirecting or retrying an unsafe POST."""
    logger.warning(
        "CSRF rejected path=%s host=%s origin=%s referer=%s session_present=%s reason=%s",
        request.path,
        request.META.get("HTTP_HOST", ""),
        request.META.get("HTTP_ORIGIN", ""),
        request.META.get("HTTP_REFERER", ""),
        bool(request.session.session_key),
        reason,
    )
    return HttpResponse(
        "Security verification failed. Reload the form page and submit it again.",
        status=403,
        content_type="text/plain; charset=utf-8",
    )
