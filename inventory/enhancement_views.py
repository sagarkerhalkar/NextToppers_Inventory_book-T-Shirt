from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .enhanced_forms import TshirtStockThresholdForm
from .forms import EmployeeRecordForm, TshirtBrandForm
from .models import BookAllocation, TshirtAllocation, TshirtBrand, TshirtStock, User
from .permissions import role_required
from .services import audit, free_entitlement


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_record_create(request):
    form = EmployeeRecordForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        audit(request.user, "INVENTORY_ONLY_EMPLOYEE_CREATED", employee, f"Created inventory-only employee {employee.employee_id}")
        messages.success(request, "Employee record created without login access.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": "Add Employee Without Login",
        "help_text": "This employee can receive Books and T-shirts but cannot sign in to the application.",
    })


@login_required
def employee_history(request, pk):
    employee = get_object_or_404(User, pk=pk)
    book_history = BookAllocation.objects.select_related("book", "allocated_by", "returned_by").filter(employee=employee)
    tshirt_history = TshirtAllocation.objects.select_related("stock", "stock__brand", "requested_by", "issued_by", "approved_by").filter(employee=employee)
    entitlement_rows = [{"brand": brand, **free_entitlement(employee, brand)} for brand in TshirtBrand.objects.filter(is_active=True).order_by("name")]
    return render(request, "inventory/employees/history.html", {
        "employee": employee,
        "book_history": book_history,
        "tshirt_history": tshirt_history,
        "entitlement_rows": entitlement_rows,
    })


@login_required
def book_history(request):
    allocations = BookAllocation.objects.select_related("book", "employee", "allocated_by", "returned_by").all()
    return render(request, "inventory/books/history.html", {"allocations": allocations})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_list(request):
    brands = TshirtBrand.objects.all().order_by("name")
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
        messages.success(request, "Brand and free entitlement updated.")
        return redirect("inventory:tshirt_brand_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Edit Brand: {brand.name}"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_deactivate(request, pk):
    brand = get_object_or_404(TshirtBrand, pk=pk)
    if request.method == "POST":
        brand.is_active = False
        brand.save(update_fields=["is_active", "updated_at"])
        audit(request.user, "TSHIRT_BRAND_DEACTIVATED", brand, f"Deactivated brand {brand.name}")
        messages.success(request, "Brand deactivated. Existing history and stock remain preserved.")
    return redirect("inventory:tshirt_brand_list")


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_stock_threshold_edit(request, pk):
    stock = get_object_or_404(TshirtStock.objects.select_related("brand"), pk=pk)
    form = TshirtStockThresholdForm(request.POST or None, instance=stock)
    if request.method == "POST" and form.is_valid():
        form.save()
        audit(request.user, "TSHIRT_LOW_STOCK_LIMIT_UPDATED", stock, f"Updated {stock.brand.name}/{stock.size} low-stock limit")
        messages.success(request, "Low-stock alert limit updated.")
        return redirect("inventory:tshirt_stock_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Low-stock Limit: {stock.brand.name} / {stock.size}"})
