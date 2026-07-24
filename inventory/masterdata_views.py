from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect

from .models import AuditLog, Employee, User
from .permissions import can_manage_target, role_required


def _record_deletion(actor, entity_type, entity_id, description, metadata=None):
    AuditLog.objects.create(
        actor=actor,
        action=f"{entity_type.upper()}_DELETED",
        entity_type=entity_type,
        entity_id=str(entity_id),
        description=description,
        metadata=metadata or {},
    )


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method != "POST":
        return redirect("inventory:employee_list")

    employee_id = employee.employee_id
    employee_name = employee.full_name
    try:
        employee.delete()
    except ProtectedError:
        messages.error(
            request,
            "This employee cannot be deleted because Book or T-shirt history is linked to the record. "
            "Edit the employee and mark the status inactive instead.",
        )
    else:
        _record_deletion(
            request.user,
            "Employee",
            pk,
            f"Deleted employee {employee_id} - {employee_name}",
            {"employee_id": employee_id, "full_name": employee_name},
        )
        messages.success(request, f"Employee {employee_id} deleted successfully.")
    return redirect("inventory:employee_list")


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def login_user_delete(request, pk):
    login_user = get_object_or_404(User, pk=pk)
    if request.method != "POST":
        return redirect("inventory:login_user_list")

    if login_user.pk == request.user.pk:
        messages.error(request, "You cannot delete the account currently signed in.")
        return redirect("inventory:login_user_list")

    if not can_manage_target(request.user, login_user):
        messages.error(request, "You cannot delete this login user.")
        return redirect("inventory:login_user_list")

    active_super_admins = User.objects.filter(role=User.Role.SUPER_ADMIN, is_active=True).count()
    if login_user.role == User.Role.SUPER_ADMIN and login_user.is_active and active_super_admins <= 1:
        messages.error(request, "The last active Super Admin cannot be deleted.")
        return redirect("inventory:login_user_list")

    employee_id = login_user.employee_id
    full_name = login_user.full_name
    role = login_user.role
    try:
        login_user.delete()
    except ProtectedError:
        messages.error(
            request,
            "This login user cannot be deleted because protected historical inventory is linked to the account. "
            "Edit the account and deactivate it instead.",
        )
    else:
        _record_deletion(
            request.user,
            "LoginUser",
            pk,
            f"Deleted login user {employee_id} - {full_name}",
            {"employee_id": employee_id, "full_name": full_name, "role": role},
        )
        messages.success(request, f"Login user {employee_id} deleted successfully.")
    return redirect("inventory:login_user_list")
