import json

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from .models import AuditLog, Book, BookAllocation, Employee, TshirtAllocation, TshirtStock, User


@login_required
def dashboard(request):
    stock_rows = list(
        TshirtStock.objects.select_related("brand")
        .filter(brand__is_active=True)
        .order_by("brand__name", "size")
    )

    brand_totals = {}
    for row in stock_rows:
        entry = brand_totals.setdefault(row.brand.name, {"available": 0, "allocated": 0})
        entry["available"] += row.available_quantity
        entry["allocated"] += row.allocated_quantity

    book_total = Book.objects.filter(is_active=True).count()
    book_available = Book.objects.filter(is_active=True, status=Book.Status.IN_LIBRARY).count()
    book_allocated = Book.objects.filter(is_active=True, status=Book.Status.ALLOCATED).count()
    book_damaged = Book.objects.filter(is_active=True, condition=Book.Condition.DAMAGED).count()
    book_lost = Book.objects.filter(is_active=True, condition=Book.Condition.LOST).count()
    book_returned = BookAllocation.objects.filter(is_active=False, returned_at__isnull=False).count()

    tshirt_available = sum(row.available_quantity for row in stock_rows)
    tshirt_allocated_stock = sum(row.allocated_quantity for row in stock_rows)
    tshirt_total = tshirt_available + tshirt_allocated_stock
    tshirt_free_issued = (
        TshirtAllocation.objects.filter(
            issue_type=TshirtAllocation.IssueType.FREE,
            status=TshirtAllocation.Status.ISSUED,
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    tshirt_paid_issued = (
        TshirtAllocation.objects.filter(
            issue_type=TshirtAllocation.IssueType.PAID,
            status=TshirtAllocation.Status.ISSUED,
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    pending_paid = TshirtAllocation.objects.filter(
        issue_type=TshirtAllocation.IssueType.PAID,
        status=TshirtAllocation.Status.PENDING,
    ).count()

    recent_books = list(
        BookAllocation.objects.select_related(
            "book", "employee", "employee_record", "allocated_by", "returned_by"
        )[:8]
    )
    recent_tshirts = list(
        TshirtAllocation.objects.select_related(
            "stock", "stock__brand", "employee", "employee_record", "issued_by", "requested_by"
        )[:8]
    )

    context = {
        "employee_total": Employee.objects.filter(is_active=True).count(),
        "book_total": book_total,
        "book_available": book_available,
        "book_allocated": book_allocated,
        "book_returned": book_returned,
        "book_damaged": book_damaged,
        "book_lost": book_lost,
        "book_problem": book_damaged + book_lost,
        "tshirt_total": tshirt_total,
        "tshirt_available": tshirt_available,
        "tshirt_allocated": tshirt_allocated_stock,
        "tshirt_free_issued": tshirt_free_issued,
        "tshirt_paid_issued": tshirt_paid_issued,
        "pending_paid": pending_paid,
        "low_stock": sum(1 for row in stock_rows if row.is_low_stock),
        "recent_books": recent_books,
        "recent_tshirts": recent_tshirts,
        "recent_audit": AuditLog.objects.select_related("actor")[:8]
        if request.user.role == User.Role.SUPER_ADMIN
        else [],
        "brand_chart_labels": json.dumps(list(brand_totals.keys())),
        "brand_available_data": json.dumps([value["available"] for value in brand_totals.values()]),
        "brand_allocated_data": json.dumps([value["allocated"] for value in brand_totals.values()]),
        "book_chart_data": json.dumps([book_available, book_allocated, book_damaged, book_lost]),
        "tshirt_chart_data": json.dumps([tshirt_available, tshirt_free_issued, tshirt_paid_issued, pending_paid]),
    }
    return render(request, "inventory/dashboard.html", context)
