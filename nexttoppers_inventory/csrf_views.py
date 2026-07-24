from __future__ import annotations

import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

logger = logging.getLogger("django.security.csrf")


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    """Log useful reverse-proxy details and refresh a failed login CSRF cookie.

    The redirect is deliberately limited to the login endpoint. Other CSRF failures
    remain explicit 403 responses so unsafe POST actions are never silently retried.
    """
    logger.warning(
        "CSRF rejected path=%s host=%s origin=%s referer=%s cookie_present=%s reason=%s",
        request.path,
        request.META.get("HTTP_HOST", ""),
        request.META.get("HTTP_ORIGIN", ""),
        request.META.get("HTTP_REFERER", ""),
        bool(request.COOKIES.get(settings.CSRF_COOKIE_NAME)),
        reason,
    )

    if request.path.startswith("/login/") and request.GET.get("csrf") != "refreshed":
        response = redirect("/login/?csrf=refreshed")
        response.delete_cookie(
            settings.CSRF_COOKIE_NAME,
            path=settings.CSRF_COOKIE_PATH,
            domain=settings.CSRF_COOKIE_DOMAIN,
            samesite=settings.CSRF_COOKIE_SAMESITE,
        )
        return response

    return HttpResponse(
        "Security verification failed. Reload the page and submit the form again.",
        status=403,
        content_type="text/plain; charset=utf-8",
    )
