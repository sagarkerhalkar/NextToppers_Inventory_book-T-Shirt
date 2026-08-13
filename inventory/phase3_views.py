from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import BookAllocation, TshirtAllocation, TshirtBrand, TshirtStock, User
from .permissions import role_required
from .services import audit, free_entitlement
from .phase3_forms import EmployeeRecipientForm, EnableLoginForm, TshirtBrandForm


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_recipient_create(request):
    form = EmployeeRecipientForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        audit(request.user, "EMPLOYEE_RECIPIENT_CREATED", employee, f"Created non-login employee {employee.employee_id}")
        messages.success(request, "Employee created without login access.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add Employee (No Login)"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_enable_login(request, pk):
    employee = get_object_or_404(User, pk=pk)
    form = EnableLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        employee.set_password(form.cleaned_data["new_password"])
        employee.must_change_password = True
        employee.is_active = True
        employee.save(update_fields=["password", "must_change_password", "is_active"])
        audit(request.user, "EMPLOYEE_LOGIN_ENABLED", employee, f"Login enabled for {employee.employee_id}")
        messages.success(request, "Login access enabled. The user must change the temporary password.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Enable Login: {employee.employee_id}"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_disable_login(request, pk):
    employee = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        if employee.role == User.Role.SUPER_ADMIN:
            messages.error(request, "Super Admin login cannot be disabled here.")
        else:
            employee.set_unusable_password()
            employee.save(update_fields=["password"])
            audit(request.user, "EMPLOYEE_LOGIN_DISABLED", employee, f"Login disabled for {employee.employee_id}")
            messages.success(request, "Login access disabled. Inventory history remains unchanged.")
    return redirect("inventory:employee_list")


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_history(request, pk):
    employee = get_object_or_404(User, pk=pk)
    book_history = BookAllocation.objects.filter(employee=employee).select_related(
        "book", "allocated_by", "returned_by"
    ).order_by("-allocated_at")
    tshirt_history = TshirtAllocation.objects.filter(employee=employee).select_related(
        "stock", "stock__brand", "requested_by", "approved_by", "issued_by"
    ).order_by("-requested_at")
    entitlement = []
    for brand in TshirtBrand.objects.filter(is_active=True).order_by("name"):
        summary = free_entitlement(employee, brand)
        entitlement.append({"brand": brand, **summary})
    return render(request, "inventory/employees/history.html", {
        "employee": employee,
        "book_history": book_history,
        "tshirt_history": tshirt_history,
        "entitlement": entitlement,
    })


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def book_history(request):
    allocations = BookAllocation.objects.select_related(
        "book", "employee", "allocated_by", "returned_by"
    ).order_by("-allocated_at")
    return render(request, "inventory/books/history.html", {"allocations": allocations})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_list(request):
    brands = TshirtBrand.objects.prefetch_related("stock_items").order_by("name")
    return render(request, "inventory/tshirts/brand_list.html", {"brands": brands})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_create(request):
    form = TshirtBrandForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        brand = form.save()
        for size, _label in User.TshirtSize.choices:
            TshirtStock.objects.get_or_create(brand=brand, size=size)
        audit(request.user, "TSHIRT_BRAND_CREATED", brand, f"Created brand {brand.name}")
        messages.success(request, "T-shirt brand and all size stock rows created.")
        return redirect("inventory:tshirt_brand_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add T-shirt Brand"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_edit(request, pk):
    brand = get_object_or_404(TshirtBrand, pk=pk)
    form = TshirtBrandForm(request.POST or None, instance=brand)
    if request.method == "POST" and form.is_valid():
        form.save()
        for size, _label in User.TshirtSize.choices:
            TshirtStock.objects.get_or_create(brand=brand, size=size)
        audit(request.user, "TSHIRT_BRAND_EDITED", brand, f"Updated brand {brand.name}")
        messages.success(request, "Brand name, status and free allowance updated.")
        return redirect("inventory:tshirt_brand_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Edit Brand: {brand.name}"})
