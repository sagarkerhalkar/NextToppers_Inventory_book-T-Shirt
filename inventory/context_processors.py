from .models import BrandingSettings


def branding(request):
    try:
        return {"branding": BrandingSettings.load()}
    except Exception:
        return {"branding": None}
