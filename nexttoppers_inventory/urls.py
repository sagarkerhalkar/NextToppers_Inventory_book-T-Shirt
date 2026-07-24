from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.static import serve

from .auth_views import InternalNonceLoginView, internal_logout


def health_check(request):
    return HttpResponse("NEXT_TOPPERS_INVENTORY_OK", content_type="text/plain")


@login_required
def session_csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@login_required
@require_POST
def session_csrf_probe(request):
    return HttpResponse("SESSION_CSRF_OK", content_type="text/plain")


def branding_media(request, path):
    """Serve only public branding images in production.

    Private inventory documents remain available only through their protected
    document views and are not exposed by this route.
    """
    normalized = Path(path)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise Http404("Invalid branding asset path")
    return serve(request, str(normalized), document_root=settings.MEDIA_ROOT / "branding")


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("health/session-csrf-token/", session_csrf_token, name="session_csrf_token"),
    path("health/session-csrf-probe/", session_csrf_probe, name="session_csrf_probe"),
    path("admin/", admin.site.urls),
    path("login/", csrf_exempt(InternalNonceLoginView.as_view()), name="login"),
    path("logout/", csrf_exempt(internal_logout), name="logout"),
    re_path(r"^media/branding/(?P<path>.+)$", branding_media, name="branding_media"),
    path("", include("inventory.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
