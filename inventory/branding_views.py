import secrets

from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import BrandingForm
from .models import BrandingSettings, User
from .permissions import role_required
from .services import audit


BRANDING_NONCE_KEY = "_nexttoppers_branding_nonce"


def _issue_branding_nonce(request):
    nonce = secrets.token_urlsafe(32)
    request.session[BRANDING_NONCE_KEY] = nonce
    request.session.modified = True
    return nonce


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def branding_settings(request):
    branding = BrandingSettings.load()

    if request.method == "POST":
        supplied = request.POST.get("branding_nonce", "")
        expected = request.session.pop(BRANDING_NONCE_KEY, "")
        nonce_valid = bool(supplied and expected) and secrets.compare_digest(supplied, expected)
        next_nonce = _issue_branding_nonce(request)
        form = BrandingForm(request.POST, request.FILES, instance=branding)

        if not nonce_valid:
            form.add_error(None, "The branding page expired. Reload the page and submit it again.")
        elif form.is_valid():
            saved = form.save()
            audit(request.user, "BRANDING_UPDATED", saved, "Updated application branding and dashboard logo")
            messages.success(request, "Branding and logo updated successfully.")
            return redirect("inventory:branding")
    else:
        form = BrandingForm(instance=branding)
        next_nonce = _issue_branding_nonce(request)

    response = render(
        request,
        "inventory/branding_settings.html",
        {
            "form": form,
            "branding_record": branding,
            "branding_nonce": next_nonce,
            "title": "Branding Settings",
        },
    )
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    return response
