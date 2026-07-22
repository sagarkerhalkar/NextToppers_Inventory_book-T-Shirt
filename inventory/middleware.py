from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """Require users with an administrator-reset password to choose a new password."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.must_change_password:
            allowed = {reverse("inventory:change_temporary_password"), reverse("logout")}
            if request.path not in allowed and not request.path.startswith("/static/") and not request.path.startswith("/media/"):
                return redirect("inventory:change_temporary_password")
        return self.get_response(request)
