from __future__ import annotations

import secrets

from django.contrib.auth import views as auth_views
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class InternalNonceLoginView(auth_views.LoginView):
    """Login protected by a one-time server-side nonce instead of a CSRF cookie.

    The IIS deployment was intermittently rejecting the browser login POST before
    authentication.  This view keeps login-CSRF protection without depending on
    the separate CSRF cookie: a nonce is stored in the pre-authentication session
    and must be returned by the form exactly once.
    """

    template_name = "registration/login.html"
    nonce_session_key = "_nexttoppers_login_nonce"
    old_cookie_names = (
        "csrftoken",
        "sessionid",
        "nexttoppers_csrf_v2",
        "nexttoppers_session_v2",
    )

    def _issue_nonce(self) -> str:
        nonce = secrets.token_urlsafe(32)
        self.request.session[self.nonce_session_key] = nonce
        self.request.session.modified = True
        return nonce

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nonce = self.request.session.get(self.nonce_session_key) or self._issue_nonce()
        context["login_nonce"] = nonce
        return context

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        for cookie_name in self.old_cookie_names:
            response.delete_cookie(cookie_name, path="/")
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        return response

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        supplied = request.POST.get("login_nonce", "")
        expected = request.session.pop(self.nonce_session_key, "")
        nonce_is_valid = bool(supplied and expected) and secrets.compare_digest(supplied, expected)

        # Rotate immediately so an invalid-password response gets a fresh nonce.
        self._issue_nonce()

        if not nonce_is_valid:
            form = self.get_form()
            form.add_error(None, "The login page expired. Please submit the form again.")
            return self.form_invalid(form)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session.pop(self.nonce_session_key, None)
        return super().form_valid(form)
