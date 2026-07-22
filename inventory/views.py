import shutil
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.db import models
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from .forms import (
    AdminPasswordResetForm, BookAllocationForm, BookForm, BookReturnForm, BrandingForm,
    EmployeeCreateForm, EmployeeUpdateForm, FreeTshirtIssueForm, PaidTshirtRequestForm,
    RejectionForm, TshirtPurchaseForm,
)
from .models import AuditLog, Book, BookAllocation, BrandingSettings, TshirtAllocation, TshirtStock, User
from .permissions import can_manage_target, role_required
from .services import (
    add_tshirt_purchase, allocate_book, approve_paid_tshirt_request, audit,
    create_paid_tshirt_request, issue_free_tshirts, reject_paid_tshirt_request, return_book,
)


@login_required
def change_temporary_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", "form-control")
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.must_change_password = False
        user.save(update_fields=["must_change_password"])
        update_session_auth_hash(request, user)
        audit(user, "TEMPORARY_PASSWORD_CHANGED", user, "User changed an administrator-reset temporary password")
        messages.success(request, "Your new password has been saved.")
        return redirect("inventory:dashboard")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Create New Password"})


@login_required
def dashboard(request):
    context = {
        "book_total": Book.objects.filter(is_active=True).count(),
        "book_available": Book.objects.filter(is_active=True, status=Book.Status.IN_LIBRARY).count(),
        "book_allocated": Book.objects.filter(is_active=True, status=Book.Status.ALLOCATED).count(),
        "book_problem": Book.objects.filter(is_active=True, condition__in=[Book.Condition.DAMAGED, Book.Condition.LOST]).count(),
        "tshirt_available": sum(TshirtStock.objects.values_list("available_quantity", flat=True)),
        "low_stock": sum(1 for stock in TshirtStock.objects.all() if stock.is_low_stock),
        "pending_paid": TshirtAllocation.objects.filter(status=TshirtAllocation.Status.PENDING).count(),
        "recent_audit": AuditLog.objects.select_related("actor")[:10] if request.user.role == User.Role.SUPER_ADMIN else [],
    }
    return render(request, "inventory/dashboard.html", context)


@login_required
def book_list(request):
    books = Book.objects.filter(is_active=True)
    query = request.GET.get("q", "").strip()
    if query:
        books = books.filter(models.Q(asset_id__icontains=query) | models.Q(name__icontains=query) | models.Q(isbn__icontains=query))
    return render(request, "inventory/books/list.html", {"books": books, "query": query})


@login_required
def book_create(request):
    form = BookForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        book = form.save(commit=False)
        book.created_by = request.user
        book.save()
        audit(request.user, "BOOK_CREATED", book, f"Created {book.asset_id}")
        messages.success(request, f"Book {book.asset_id} created.")
        return redirect("inventory:book_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add Book"})


@login_required
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk, is_active=True)
    form = BookForm(request.POST or None, request.FILES or None, instance=book)
    if request.method == "POST" and form.is_valid():
        form.save()
        audit(request.user, "BOOK_EDITED", book, f"Edited {book.asset_id}")
        messages.success(request, "Book updated.")
        return redirect("inventory:book_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Edit {book.asset_id}", "readonly_value": book.asset_id})


@login_required
def book_allocate_view(request, pk):
    book = get_object_or_404(Book, pk=pk, is_active=True)
    form = BookAllocationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            allocate_book(book=book, employee=form.cleaned_data["employee"], actor=request.user)
            messages.success(request, "Book allocated successfully.")
            return redirect("inventory:book_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Allocate {book.asset_id}"})


@login_required
def book_return_view(request, pk):
    allocation = get_object_or_404(BookAllocation, pk=pk, is_active=True)
    form = BookReturnForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            return_book(allocation=allocation, condition=form.cleaned_data["return_condition"], note=form.cleaned_data["return_note"], actor=request.user)
            messages.success(request, "Book return recorded.")
            return redirect("inventory:book_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Return {allocation.book.asset_id}"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        try:
            asset = book.asset_id
            audit(request.user, "BOOK_DELETE_REQUESTED", book, f"Delete requested for {asset}")
            book.delete()
            messages.success(request, "Book deleted.")
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
    return redirect("inventory:book_list")


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_list(request):
    employees = User.objects.order_by("employee_id")
    return render(request, "inventory/employees/list.html", {"employees": employees})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_create(request):
    form = EmployeeCreateForm(request.POST or None, request.FILES or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        audit(request.user, "EMPLOYEE_CREATED", employee, f"Created {employee.employee_id}")
        messages.success(request, "Employee created.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add Employee"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_edit(request, pk):
    employee = get_object_or_404(User, pk=pk)
    if not can_manage_target(request.user, employee):
        messages.error(request, "You cannot manage this account.")
        return redirect("inventory:employee_list")
    form = EmployeeUpdateForm(request.POST or None, request.FILES or None, instance=employee, actor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        audit(request.user, "EMPLOYEE_EDITED", employee, f"Edited {employee.employee_id}")
        messages.success(request, "Employee updated.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Edit {employee.employee_id}", "readonly_value": employee.employee_id})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_reset_password(request, pk):
    employee = get_object_or_404(User, pk=pk)
    if not can_manage_target(request.user, employee):
        messages.error(request, "You cannot reset this account.")
        return redirect("inventory:employee_list")
    form = AdminPasswordResetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        employee.set_password(form.cleaned_data["new_password"])
        employee.must_change_password = True
        employee.save(update_fields=["password", "must_change_password"])
        audit(request.user, "PASSWORD_RESET", employee, f"Reset password for {employee.employee_id}")
        messages.success(request, "Temporary password set. The employee must change it at next sign-in.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Reset password: {employee.employee_id}"})


@login_required
def tshirt_stock_list(request):
    stocks = TshirtStock.objects.select_related("brand").all()
    return render(request, "inventory/tshirts/stock_list.html", {"stocks": stocks})


@login_required
def tshirt_purchase_create(request):
    form = TshirtPurchaseForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        stock = data.pop("stock")
        quantity = data.pop("quantity")
        add_tshirt_purchase(stock=stock, quantity=quantity, actor=request.user, **data)
        messages.success(request, "T-shirt purchase and stock update saved.")
        return redirect("inventory:tshirt_stock_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add T-shirt Purchase"})


@login_required
def free_tshirt_issue(request):
    form = FreeTshirtIssueForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            issue_free_tshirts(employee=form.cleaned_data["employee"], stock=form.cleaned_data["stock"], quantity=form.cleaned_data["quantity"], actor=request.user)
            messages.success(request, "Free T-shirt issued.")
            return redirect("inventory:tshirt_allocation_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Issue Free T-shirt"})


@login_required
def paid_tshirt_request(request):
    form = PaidTshirtRequestForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            create_paid_tshirt_request(actor=request.user, **form.cleaned_data)
            messages.success(request, "Paid T-shirt request submitted.")
            return redirect("inventory:tshirt_allocation_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Paid T-shirt Request"})


@login_required
def tshirt_allocation_list(request):
    allocations = TshirtAllocation.objects.select_related("employee", "stock", "stock__brand", "requested_by", "approved_by")
    return render(request, "inventory/tshirts/allocation_list.html", {"allocations": allocations})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def paid_tshirt_approve(request, pk):
    allocation = get_object_or_404(TshirtAllocation, pk=pk)
    if request.method == "POST":
        try:
            approve_paid_tshirt_request(allocation=allocation, actor=request.user)
            messages.success(request, "Paid T-shirt request approved and stock issued.")
        except (ValueError, PermissionError) as exc:
            messages.error(request, str(exc))
    return redirect("inventory:tshirt_allocation_list")


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def paid_tshirt_reject(request, pk):
    allocation = get_object_or_404(TshirtAllocation, pk=pk)
    form = RejectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        reject_paid_tshirt_request(allocation=allocation, reason=form.cleaned_data["rejection_reason"], actor=request.user)
        messages.success(request, "Paid T-shirt request rejected.")
        return redirect("inventory:tshirt_allocation_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Reject Paid T-shirt Request"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def branding_settings(request):
    branding = BrandingSettings.load()
    form = BrandingForm(request.POST or None, request.FILES or None, instance=branding)
    if request.method == "POST" and form.is_valid():
        form.save()
        audit(request.user, "BRANDING_UPDATED", branding, "Updated application branding")
        messages.success(request, "Branding updated.")
        return redirect("inventory:branding")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Branding Settings"})


@login_required
def reports_index(request):
    return render(request, "inventory/reports/index.html")


@role_required(User.Role.SUPER_ADMIN)
def download_database_backup(request):
    source = Path(settings.DATABASES["default"]["NAME"])
    if not source.exists():
        messages.error(request, "Database file is not available for backup.")
        return redirect("inventory:dashboard")
    settings.BACKUP_DIRECTORY.mkdir(parents=True, exist_ok=True)
    timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    destination = settings.BACKUP_DIRECTORY / f"nexttoppers_inventory_{timestamp}.sqlite3"
    shutil.copy2(source, destination)
    audit(request.user, "DATABASE_BACKUP_DOWNLOADED", request.user, destination.name)
    return FileResponse(destination.open("rb"), as_attachment=True, filename=destination.name)


def _excel_response(filename, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    output = BytesIO()
    wb.save(output)
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_books_excel(request):
    rows = Book.objects.filter(is_active=True).values_list("asset_id", "name", "class_name", "stream_name", "isbn", "condition", "status")
    return _excel_response("book_inventory.xlsx", ["Asset ID", "Book", "Class", "Stream", "ISBN", "Condition", "Status"], rows)


@login_required
def export_tshirts_excel(request):
    rows = TshirtStock.objects.select_related("brand").values_list("brand__name", "size", "available_quantity", "allocated_quantity", "low_stock_threshold")
    return _excel_response("tshirt_stock.xlsx", ["Brand", "Size", "Available", "Allocated", "Low-stock threshold"], rows)


@login_required
def export_books_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="book_inventory.pdf"'
    pdf = canvas.Canvas(response, pagesize=landscape(A4))
    _, height = landscape(A4)
    y = height - 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, "Next Toppers Book Inventory")
    y -= 28
    pdf.setFont("Helvetica", 8)
    for book in Book.objects.filter(is_active=True)[:5000]:
        line = f"{book.asset_id} | {book.name[:50]} | {book.class_name} | {book.isbn} | {book.get_condition_display()} | {book.get_status_display()}"
        pdf.drawString(40, y, line)
        y -= 14
        if y < 30:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 8)
    pdf.save()
    return response
