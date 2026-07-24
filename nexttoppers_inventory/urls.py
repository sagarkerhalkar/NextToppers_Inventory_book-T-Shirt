from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.urls import include, path
from django.views.decorators.http import require_POST

from .auth_views import InternalNonceLoginView


def health_check(request):
    return HttpResponse("NEXT_TOPPERS_INVENTORY_OK", content_type="text/plain")


@login_required
def session_csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@login_required
@require_POST
def session_csrf_probe(request):
    return HttpResponse("SESSION_CSRF_OK", content_type="text/plain")


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("health/session-csrf-token/", session_csrf_token, name="session_csrf_token"),
    path("health/session-csrf-probe/", session_csrf_probe, name="session_csrf_probe"),
    path("admin/", admin.site.urls),
    path("login/", InternalNonceLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("inventory.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
