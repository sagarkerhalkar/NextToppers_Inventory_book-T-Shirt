from __future__ import annotations

import secrets

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic.edit import FormView


class InternalNonceLoginView(FormView):
    """Authenticate with a one-time server-side nonce instead of a CSRF cookie.

    Django's built-in LoginView adds an internal csrf_protect decorator. This
    standalone FormView intentionally avoids that wrapper while preserving the
    same AuthenticationForm, password validation, session rotation and safe
    redirect behaviour.
    """

    template_name = "registration/login.html"
    form_class = AuthenticationForm
    redirect_field_name = REDIRECT_FIELD_NAME
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

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nonce = self.request.session.get(self.nonce_session_key) or self._issue_nonce()
        redirect_value = self.get_redirect_url()
        context["login_nonce"] = nonce
        context["redirect_field_name"] = self.redirect_field_name
        context["redirect_field_value"] = redirect_value
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

        # Every POST rotates the nonce. An invalid-password response therefore gets
        # a fresh value and an old browser form cannot be replayed.
        self._issue_nonce()

        if not nonce_is_valid:
            form = self.get_form()
            form.add_error(None, "The login page expired. Please submit the form again.")
            return self.form_invalid(form)

        return super().post(request, *args, **kwargs)

    def get_redirect_url(self) -> str:
        candidate = self.request.POST.get(self.redirect_field_name) or self.request.GET.get(self.redirect_field_name)
        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return ""

    def get_success_url(self) -> str:
        return self.get_redirect_url() or resolve_url(settings.LOGIN_REDIRECT_URL)

    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        self.request.session.pop(self.nonce_session_key, None)
        auth_login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())
