import json
import shutil
from io import BytesIO
from pathlib import Path

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openpyxl import Workbook
from reportlab.graphics.barcode import code128
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .forms import (
    AdminPasswordResetForm, BookAllocationForm, BookForm, BookReturnForm, BrandingForm,
    EmployeeRecordForm, FreeTshirtIssueForm, LoginUserCreateForm, LoginUserUpdateForm,
    PaidTshirtRequestForm, RejectionForm, TshirtPurchaseForm,
)
from .models import AuditLog, Book, BookAllocation, BrandingSettings, Employee, TshirtAllocation, TshirtStock, User
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
        audit(user, "TEMPORARY_PASSWORD_CHANGED", user, "Login user changed an administrator-reset temporary password")
        messages.success(request, "Your new password has been saved.")
        return redirect("inventory:dashboard")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Create New Password"})


@login_required
def dashboard(request):
    stock_rows = list(TshirtStock.objects.select_related("brand").filter(brand__is_active=True).order_by("brand__name", "size"))
    brand_totals = {}
    for row in stock_rows:
        entry = brand_totals.setdefault(row.brand.name, {"available": 0, "allocated": 0})
        entry["available"] += row.available_quantity
        entry["allocated"] += row.allocated_quantity

    activity = []
    for row in BookAllocation.objects.select_related("book", "employee", "employee_record", "allocated_by")[:8]:
        activity.append({"time": row.allocated_at, "kind": "Book", "title": f"{row.book.asset_id} · {row.book.name}", "employee": row.recipient, "actor": row.allocated_by})
    for row in TshirtAllocation.objects.select_related("stock", "stock__brand", "employee", "employee_record", "issued_by").filter(status=TshirtAllocation.Status.ISSUED)[:8]:
        activity.append({"time": row.issued_at or row.requested_at, "kind": "T-shirt", "title": f"{row.stock.brand.name} / {row.stock.size} × {row.quantity}", "employee": row.recipient, "actor": row.issued_by or row.requested_by})
    activity.sort(key=lambda item: item["time"] or timezone.now(), reverse=True)

    context = {
        "employee_total": Employee.objects.filter(is_active=True).count(),
        "book_total": Book.objects.filter(is_active=True).count(),
        "book_available": Book.objects.filter(is_active=True, status=Book.Status.IN_LIBRARY).count(),
        "book_allocated": Book.objects.filter(is_active=True, status=Book.Status.ALLOCATED).count(),
        "book_problem": Book.objects.filter(is_active=True, condition__in=[Book.Condition.DAMAGED, Book.Condition.LOST]).count(),
        "tshirt_available": sum(row.available_quantity for row in stock_rows),
        "low_stock": sum(1 for row in stock_rows if row.is_low_stock),
        "pending_paid": TshirtAllocation.objects.filter(status=TshirtAllocation.Status.PENDING).count(),
        "recent_activity": activity[:10],
        "recent_audit": AuditLog.objects.select_related("actor")[:8] if request.user.role == User.Role.SUPER_ADMIN else [],
        "brand_chart_labels": json.dumps(list(brand_totals.keys())),
        "brand_available_data": json.dumps([value["available"] for value in brand_totals.values()]),
        "brand_allocated_data": json.dumps([value["allocated"] for value in brand_totals.values()]),
        "book_chart_data": json.dumps([
            Book.objects.filter(is_active=True, status=Book.Status.IN_LIBRARY).count(),
            Book.objects.filter(is_active=True, status=Book.Status.ALLOCATED).count(),
            Book.objects.filter(is_active=True, condition=Book.Condition.DAMAGED).count(),
            Book.objects.filter(is_active=True, condition=Book.Condition.LOST).count(),
        ]),
    }
    return render(request, "inventory/dashboard.html", context)


@login_required
def book_list(request):
    active_allocations = BookAllocation.objects.filter(is_active=True).select_related("employee", "employee_record", "allocated_by")
    books = Book.objects.filter(is_active=True).prefetch_related(Prefetch("allocations", queryset=active_allocations, to_attr="active_allocations"))
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
            messages.success(request, "Book allocated successfully with date and time recorded.")
            return redirect("inventory:book_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Allocate {book.asset_id}"})


@login_required
def book_return_view(request, pk):
    allocation = get_object_or_404(BookAllocation.objects.select_related("book"), pk=pk, is_active=True)
    form = BookReturnForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            return_book(allocation=allocation, condition=form.cleaned_data["return_condition"], note=form.cleaned_data["return_note"], actor=request.user)
            messages.success(request, "Book return date, time, condition and note were recorded.")
            return redirect("inventory:book_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Return {allocation.book.asset_id}"})


@login_required
def book_asset_label(request, pk):
    book = get_object_or_404(Book, pk=pk)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{book.asset_id}_label.pdf"'
    pdf = canvas.Canvas(response, pagesize=(360, 210))
    pdf.setTitle(f"{book.asset_id} Book Label")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(18, 184, "Next Toppers Book Asset")
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(18, 160, book.asset_id)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(18, 145, book.name[:55])
    barcode = code128.Code128(book.asset_id, barHeight=38, barWidth=1.1)
    barcode.drawOn(pdf, 18, 82)
    qr_buffer = BytesIO()
    qrcode.make(book.asset_id).save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    pdf.drawImage(ImageReader(qr_buffer), 255, 82, 76, 76, preserveAspectRatio=True, mask="auto")
    pdf.setFont("Helvetica", 8)
    pdf.drawString(18, 62, "Scan QR or barcode to identify this physical Book.")
    pdf.save()
    audit(request.user, "BOOK_LABEL_DOWNLOADED", book, f"Downloaded QR/barcode label for {book.asset_id}")
    return response


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


@login_required
def employee_list(request):
    employees = Employee.objects.all()
    query = request.GET.get("q", "").strip()
    if query:
        employees = employees.filter(models.Q(employee_id__icontains=query) | models.Q(full_name__icontains=query) | models.Q(mobile_number__icontains=query))
    return render(request, "inventory/employees/list.html", {"employees": employees, "query": query})


@login_required
def employee_create(request):
    form = EmployeeRecordForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        audit(request.user, "EMPLOYEE_CREATED", employee, f"Created non-login employee {employee.employee_id}")
        messages.success(request, "Employee record created. No login account was created.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add Employee (No Login)", "help_text": "Employees receive Books and T-shirts but do not sign in."})


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    form = EmployeeRecordForm(request.POST or None, request.FILES or None, instance=employee)
    if request.method == "POST" and form.is_valid():
        form.save()
        audit(request.user, "EMPLOYEE_EDITED", employee, f"Edited employee {employee.employee_id}")
        messages.success(request, "Employee updated.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Edit Employee {employee.employee_id}", "readonly_value": employee.employee_id})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def login_user_list(request):
    return render(request, "inventory/users/list.html", {"login_users": User.objects.order_by("employee_id")})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def login_user_create(request):
    form = LoginUserCreateForm(request.POST or None, request.FILES or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        login_user = form.save(commit=False)
        login_user.must_change_password = True
        login_user.save()
        audit(request.user, "LOGIN_USER_CREATED", login_user, f"Created login account {login_user.employee_id}")
        messages.success(request, "Login account created. The user must change the temporary password at first sign-in.")
        return redirect("inventory:login_user_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": "Add Login User"})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def login_user_edit(request, pk):
    login_user = get_object_or_404(User, pk=pk)
    if not can_manage_target(request.user, login_user):
        messages.error(request, "You cannot manage this account.")
        return redirect("inventory:login_user_list")
    form = LoginUserUpdateForm(request.POST or None, request.FILES or None, instance=login_user, actor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        audit(request.user, "LOGIN_USER_EDITED", login_user, f"Edited login account {login_user.employee_id}")
        messages.success(request, "Login user updated.")
        return redirect("inventory:login_user_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Edit Login User {login_user.employee_id}", "readonly_value": login_user.employee_id})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def employee_reset_password(request, pk):
    login_user = get_object_or_404(User, pk=pk)
    if not can_manage_target(request.user, login_user):
        messages.error(request, "You cannot reset this account.")
        return redirect("inventory:login_user_list")
    form = AdminPasswordResetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login_user.set_password(form.cleaned_data["new_password"])
        login_user.must_change_password = True
        login_user.save(update_fields=["password", "must_change_password"])
        audit(request.user, "PASSWORD_RESET", login_user, f"Reset password for {login_user.employee_id}")
        messages.success(request, "Temporary password set. The login user must change it at next sign-in.")
        return redirect("inventory:login_user_list")
    return render(request, "inventory/generic_form.html", {"form": form, "title": f"Reset password: {login_user.employee_id}"})


@login_required
def tshirt_stock_list(request):
    return render(request, "inventory/tshirts/stock_list.html", {"stocks": TshirtStock.objects.select_related("brand").all()})


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
            messages.success(request, "Free T-shirt issued with employee, date, time and acting user recorded.")
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
    allocations = TshirtAllocation.objects.select_related("employee", "employee_record", "stock", "stock__brand", "requested_by", "approved_by", "issued_by")
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
