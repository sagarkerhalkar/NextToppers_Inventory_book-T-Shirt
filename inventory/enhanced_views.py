from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .enhanced_forms import EmployeeRecipientForm, TshirtBrandForm, TshirtStockThresholdForm
from .models import Book, BookAllocation, TshirtAllocation, TshirtBrand, TshirtStock, User
from .permissions import role_required
from .services import audit, free_entitlement


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_recipient_create(request):
    form = EmployeeRecipientForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        audit(request.user, "EMPLOYEE_RECIPIENT_CREATED", employee, f"Created non-login employee {employee.employee_id}")
        messages.success(request, "Employee created as an inventory recipient. This employee cannot log in.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add Employee Without Login"})


@login_required
def employee_history(request, pk):
    employee = get_object_or_404(User, pk=pk)
    book_history = BookAllocation.objects.filter(employee=employee).select_related("book", "allocated_by", "returned_by")
    tshirt_history = TshirtAllocation.objects.filter(employee=employee).select_related("stock", "stock__brand", "requested_by", "issued_by", "approved_by")
    entitlement_rows = []
    for brand in TshirtBrand.objects.filter(is_active=True).order_by("name"):
        summary = free_entitlement(employee, brand)
        entitlement_rows.append({"brand": brand, **summary})
    return render(request, "inventory/employees/history.html", {
        "employee": employee,
        "book_history": book_history,
        "tshirt_history": tshirt_history,
        "entitlement_rows": entitlement_rows,
    })


@login_required
def book_history(request, pk):
    book = get_object_or_404(Book, pk=pk)
    allocations = book.allocations.select_related("employee", "allocated_by", "returned_by").all()
    return render(request, "inventory/books/history.html", {"book": book, "allocations": allocations})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_list(request):
    brands = TshirtBrand.objects.prefetch_related("stock_items").order_by("name")
    return render(request, "inventory/tshirts/brand_list.html", {"brands": brands})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_create(request):
    form = TshirtBrandForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        brand = form.save()
        audit(request.user, "TSHIRT_BRAND_CREATED", brand, f"Created brand {brand.name}")
        messages.success(request, f"{brand.name} created with stock rows for every size.")
        return redirect("inventory:tshirt_brand_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add T-shirt Brand"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_edit(request, pk):
    brand = get_object_or_404(TshirtBrand, pk=pk)
    form = TshirtBrandForm(request.POST or None, instance=brand)
    if request.method == "POST" and form.is_valid():
        brand = form.save()
        audit(request.user, "TSHIRT_BRAND_EDITED", brand, f"Updated brand {brand.name} and free allowance")
        messages.success(request, "Brand and free allowance updated.")
        return redirect("inventory:tshirt_brand_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Edit Brand: {brand.name}"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_stock_threshold_edit(request, pk):
    stock = get_object_or_404(TshirtStock.objects.select_related("brand"), pk=pk)
    form = TshirtStockThresholdForm(request.POST or None, instance=stock)
    if request.method == "POST" and form.is_valid():
        form.save()
        audit(request.user, "TSHIRT_LOW_STOCK_LIMIT_UPDATED", stock, f"Updated {stock.brand.name}/{stock.size} low-stock limit")
        messages.success(request, "Low-stock limit updated.")
        return redirect("inventory:tshirt_stock_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Low-stock Limit: {stock.brand.name} / {stock.size}"})
