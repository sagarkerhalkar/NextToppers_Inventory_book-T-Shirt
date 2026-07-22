from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InventoryEmployeeForm, TshirtBrandForm
from .models import Book, TshirtBrand, TshirtStock, User
from .permissions import role_required
from .services import audit, free_entitlement


@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book.objects.prefetch_related("allocations__employee", "allocations__allocated_by", "allocations__returned_by"), pk=pk)
    return render(request, "inventory/books/detail.html", {"book": book})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def inventory_employee_create(request):
    form = InventoryEmployeeForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        employee = form.save(commit=False)
        employee.role = User.Role.STAFF
        employee.is_active = True
        employee.set_unusable_password()
        employee.save()
        audit(request.user, "INVENTORY_EMPLOYEE_CREATED", employee, f"Created inventory-only employee {employee.employee_id}")
        messages.success(request, "Employee created for inventory records. Login access was not created.")
        return redirect("inventory:employee_detail", pk=employee.pk)
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add Employee Without Login", "subtitle": "This employee can receive Books and T-shirts but cannot sign in."})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_detail(request, pk):
    employee = get_object_or_404(User, pk=pk)
    book_history = employee.book_allocations.select_related("book", "allocated_by", "returned_by").all()
    tshirt_history = employee.tshirt_allocations.select_related("stock", "stock__brand", "requested_by", "issued_by", "approved_by").all()
    entitlement_rows = []
    for brand in TshirtBrand.objects.filter(is_active=True).order_by("name"):
        summary = free_entitlement(employee, brand)
        summary["brand"] = brand
        entitlement_rows.append(summary)
    return render(request, "inventory/employees/detail.html", {
        "employee": employee,
        "book_history": book_history,
        "tshirt_history": tshirt_history,
        "entitlement_rows": entitlement_rows,
        "login_enabled": employee.has_usable_password(),
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
        audit(request.user, "TSHIRT_BRAND_CREATED", brand, f"Created brand {brand.name} with allowance {brand.free_quantity_rolling_12_months}")
        messages.success(request, f"{brand.name} created with stock rows for every size.")
        return redirect("inventory:tshirt_brand_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add T-shirt Brand"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_edit(request, pk):
    brand = get_object_or_404(TshirtBrand, pk=pk)
    form = TshirtBrandForm(request.POST or None, instance=brand)
    if request.method == "POST" and form.is_valid():
        form.save()
        audit(request.user, "TSHIRT_BRAND_UPDATED", brand, f"Updated brand {brand.name} and free allowance")
        messages.success(request, "Brand and free allowance updated.")
        return redirect("inventory:tshirt_brand_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Edit Brand: {brand.name}"})
