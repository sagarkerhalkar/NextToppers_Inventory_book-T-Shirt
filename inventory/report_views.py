from datetime import date, datetime
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from .models import AuditLog, BookAllocation, TshirtAllocation, TshirtStock, User
from .permissions import role_required


def _excel_response(filename, sheet_name, headers, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name[:31]
    sheet.append(headers)
    header_fill = PatternFill("solid", fgColor="DCE6F1")
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
    for row in rows:
        normalised = []
        for value in row:
            if value is None:
                normalised.append("")
            elif isinstance(value, datetime):
                if timezone.is_aware(value):
                    value = timezone.localtime(value)
                normalised.append(value.strftime("%d-%m-%Y %H:%M:%S"))
            elif isinstance(value, date):
                normalised.append(value.strftime("%d-%m-%Y"))
            else:
                normalised.append(value)
        sheet.append(normalised)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column in sheet.columns:
        width = max(len(str(cell.value or "")) for cell in column) + 2
        sheet.column_dimensions[column[0].column_letter].width = min(max(width, 10), 45)
    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _pdf_response(filename, title, headers, rows, widths=None):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    page_size = landscape(A4)
    pdf = canvas.Canvas(response, pagesize=page_size)
    width, height = page_size
    x_start = 32
    y = height - 36
    row_height = 15
    widths = widths or [max((width - 64) / len(headers), 60)] * len(headers)

    def draw_header():
        nonlocal y
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(x_start, y, title)
        y -= 24
        pdf.setFont("Helvetica-Bold", 7)
        x = x_start
        for header, column_width in zip(headers, widths):
            pdf.drawString(x, y, str(header)[:30])
            x += column_width
        y -= row_height
        pdf.line(x_start, y + 4, width - 32, y + 4)

    draw_header()
    pdf.setFont("Helvetica", 7)
    for row in rows:
        if y < 35:
            pdf.showPage()
            y = height - 36
            draw_header()
            pdf.setFont("Helvetica", 7)
        x = x_start
        for value, column_width in zip(row, widths):
            text = str(value or "")
            max_chars = max(int(column_width / 4.2), 8)
            pdf.drawString(x, y, text[:max_chars])
            x += column_width
        y -= row_height
    pdf.save()
    return response


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def export_employees_excel(request):
    rows = User.objects.order_by("employee_id").values_list(
        "employee_id", "full_name", "mobile_number", "email", "role", "department",
        "designation", "joining_date", "office_location", "default_tshirt_size", "is_active",
    )
    return _excel_response(
        "employees.xlsx", "Employees",
        ["Employee ID", "Full name", "Mobile", "Email", "Role", "Department", "Designation", "Joining date", "Office", "T-shirt size", "Active"],
        rows,
    )


@login_required
def export_book_history_excel(request):
    rows = BookAllocation.objects.select_related("book", "employee", "allocated_by", "returned_by").values_list(
        "book__asset_id", "book__name", "employee__employee_id", "employee__full_name",
        "allocated_at", "allocated_by__employee_id", "returned_at", "return_condition",
        "return_note", "returned_by__employee_id", "is_active",
    )
    return _excel_response(
        "book_allocation_return_history.xlsx", "Book History",
        ["Asset ID", "Book", "Employee ID", "Employee", "Allocated at", "Allocated by", "Returned at", "Return condition", "Return note", "Returned by", "Active allocation"],
        rows,
    )


@login_required
def export_book_history_pdf(request):
    rows = BookAllocation.objects.select_related("book", "employee").values_list(
        "book__asset_id", "book__name", "employee__employee_id", "allocated_at", "returned_at", "return_condition", "is_active",
    )
    formatted = (
        (
            asset_id,
            book_name,
            employee_id,
            timezone.localtime(allocated_at).strftime("%d-%m-%Y %H:%M") if allocated_at else "",
            timezone.localtime(returned_at).strftime("%d-%m-%Y %H:%M") if returned_at else "",
            condition,
            "Open" if is_active else "Returned",
        )
        for asset_id, book_name, employee_id, allocated_at, returned_at, condition, is_active in rows
    )
    return _pdf_response(
        "book_allocation_return_history.pdf", "Next Toppers Book Allocation and Return History",
        ["Asset ID", "Book", "Employee", "Allocated", "Returned", "Condition", "Status"],
        formatted,
        [70, 190, 80, 105, 105, 65, 55],
    )


@login_required
def export_tshirt_allocations_excel(request):
    rows = TshirtAllocation.objects.select_related("employee", "stock", "stock__brand", "requested_by", "approved_by", "issued_by").values_list(
        "employee__employee_id", "employee__full_name", "stock__brand__name", "stock__size",
        "quantity", "issue_type", "status", "requested_at", "requested_by__employee_id",
        "payment_amount", "payment_date", "approved_by__employee_id", "approved_at",
        "issued_by__employee_id", "issued_at", "rejection_reason",
    )
    return _excel_response(
        "tshirt_allocation_history.xlsx", "T-shirt History",
        ["Employee ID", "Employee", "Brand", "Size", "Quantity", "Issue type", "Status", "Requested at", "Requested by", "Payment amount", "Payment date", "Approved by", "Approved at", "Issued by", "Issued at", "Rejection reason"],
        rows,
    )


@login_required
def export_tshirt_stock_pdf(request):
    rows = TshirtStock.objects.select_related("brand").order_by("brand__name", "size").values_list(
        "brand__name", "size", "available_quantity", "allocated_quantity", "low_stock_threshold",
    )
    formatted = (
        (brand, size, available, allocated, threshold, "LOW" if available <= threshold else "OK")
        for brand, size, available, allocated, threshold in rows
    )
    return _pdf_response(
        "tshirt_stock.pdf", "Next Toppers T-shirt Stock",
        ["Brand", "Size", "Available", "Allocated", "Threshold", "Status"],
        formatted,
        [220, 70, 90, 90, 90, 70],
    )


@login_required
def export_low_stock_excel(request):
    rows = []
    for stock in TshirtStock.objects.select_related("brand").order_by("brand__name", "size"):
        if stock.is_low_stock:
            rows.append((stock.brand.name, stock.size, stock.available_quantity, stock.allocated_quantity, stock.low_stock_threshold))
    return _excel_response(
        "low_stock.xlsx", "Low Stock",
        ["Brand", "Size", "Available", "Allocated", "Threshold"],
        rows,
    )


@role_required(User.Role.SUPER_ADMIN)
def export_audit_excel(request):
    rows = AuditLog.objects.select_related("actor").values_list(
        "created_at", "actor__employee_id", "action", "entity_type", "entity_id", "description",
    )
    return _excel_response(
        "audit_history.xlsx", "Audit History",
        ["Date and time", "Actor", "Action", "Entity type", "Entity ID", "Description"],
        rows,
    )
