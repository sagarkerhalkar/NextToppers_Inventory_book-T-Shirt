from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EmployeeRecordForm, TshirtBrandForm
from .models import BookAllocation, TshirtAllocation, TshirtBrand, TshirtStock, User
from .permissions import role_required
from .services import audit, free_entitlement


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_record_create(request):
    form = EmployeeRecordForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        audit(request.user, "EMPLOYEE_RECORD_CREATED", employee, f"Created non-login employee {employee.employee_id}")
        messages.success(request, "Employee record created without login access.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add Employee Without Login"})


@login_required
def book_history(request):
    history = BookAllocation.objects.select_related("book", "employee", "allocated_by", "returned_by")
    employee_id = request.GET.get("employee", "").strip()
    status = request.GET.get("status", "").strip()
    if employee_id:
        history = history.filter(employee__employee_id__icontains=employee_id)
    if status == "active":
        history = history.filter(is_active=True)
    elif status == "returned":
        history = history.filter(is_active=False)
    return render(request, "inventory/books/history.html", {"history": history, "employee_id": employee_id, "status": status})


@login_required
def employee_history(request, pk):
    employee = get_object_or_404(User, pk=pk)
    book_history_rows = BookAllocation.objects.filter(employee=employee).select_related("book", "allocated_by", "returned_by")
    tshirt_history_rows = TshirtAllocation.objects.filter(employee=employee).select_related("stock", "stock__brand", "requested_by", "issued_by", "approved_by")
    entitlement_rows = []
    for brand in TshirtBrand.objects.filter(is_active=True).order_by("name"):
        summary = free_entitlement(employee, brand)
        summary["brand"] = brand
        entitlement_rows.append(summary)
    return render(request, "inventory/employees/history.html", {
        "employee": employee,
        "book_history": book_history_rows,
        "tshirt_history": tshirt_history_rows,
        "entitlements": entitlement_rows,
    })


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_list(request):
    brands = TshirtBrand.objects.prefetch_related("stock_items").order_by("name")
    return render(request, "inventory/tshirts/brand_list.html", {"brands": brands})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
@transaction.atomic
def tshirt_brand_create(request):
    form = TshirtBrandForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        brand = form.save()
        for size, _label in User.TshirtSize.choices:
            TshirtStock.objects.get_or_create(brand=brand, size=size)
        audit(request.user, "TSHIRT_BRAND_CREATED", brand, f"Created brand {brand.name} with free limit {brand.free_quantity_rolling_12_months}")
        messages.success(request, f"{brand.name} added with all T-shirt sizes.")
        return redirect("inventory:tshirt_brand_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add T-shirt Brand"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_edit(request, pk):
    brand = get_object_or_404(TshirtBrand, pk=pk)
    form = TshirtBrandForm(request.POST or None, instance=brand)
    if request.method == "POST" and form.is_valid():
        form.save()
        audit(request.user, "TSHIRT_BRAND_UPDATED", brand, f"Updated {brand.name}; free limit {brand.free_quantity_rolling_12_months}")
        messages.success(request, "Brand and free entitlement updated.")
        return redirect("inventory:tshirt_brand_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Edit Brand: {brand.name}"})
