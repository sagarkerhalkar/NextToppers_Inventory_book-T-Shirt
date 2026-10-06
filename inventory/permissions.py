from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to perform this action.")
                return redirect("inventory:dashboard")
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def can_manage_target(actor, target):
    if actor.role == actor.Role.SUPER_ADMIN:
        return True
    if actor.role != actor.Role.ADMIN:
        return False
    return target.role != target.Role.SUPER_ADMIN
