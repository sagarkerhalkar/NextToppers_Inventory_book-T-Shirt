from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from .models import Book, BookAllocation, Employee, TshirtAllocation, TshirtBrand, TshirtStock, User
from .pagination import paginate_queryset
from .permissions import role_required
from .services import free_entitlement


@login_required
def book_list(request):
    active_allocations = BookAllocation.objects.filter(is_active=True).select_related(
        "employee", "employee_record", "allocated_by"
    )
    books = Book.objects.filter(is_active=True).prefetch_related(
        Prefetch("allocations", queryset=active_allocations, to_attr="active_allocations")
    ).order_by("asset_id")
    query = request.GET.get("q", "").strip()
    if query:
        books = books.filter(
            models.Q(asset_id__icontains=query)
            | models.Q(name__icontains=query)
            | models.Q(isbn__icontains=query)
            | models.Q(class_name__icontains=query)
            | models.Q(stream_name__icontains=query)
        )
    pagination = paginate_queryset(request, books)
    return render(request, "inventory/books/list.html", {
        "books": pagination["page_obj"],
        "query": query,
        **pagination,
    })


@login_required
def employee_list(request):
    employees = Employee.objects.all().order_by("employee_id")
    query = request.GET.get("q", "").strip()
    if query:
        employees = employees.filter(
            models.Q(employee_id__icontains=query)
            | models.Q(full_name__icontains=query)
            | models.Q(mobile_number__icontains=query)
            | models.Q(email__icontains=query)
            | models.Q(department__icontains=query)
            | models.Q(designation__icontains=query)
        )
    pagination = paginate_queryset(request, employees)
    return render(request, "inventory/employees/list.html", {
        "employees": pagination["page_obj"],
        "query": query,
        **pagination,
    })


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def login_user_list(request):
    users = User.objects.order_by("employee_id")
    query = request.GET.get("q", "").strip()
    if query:
        users = users.filter(
            models.Q(employee_id__icontains=query)
            | models.Q(full_name__icontains=query)
            | models.Q(mobile_number__icontains=query)
            | models.Q(email__icontains=query)
            | models.Q(role__icontains=query)
        )
    pagination = paginate_queryset(request, users)
    return render(request, "inventory/users/list.html", {
        "login_users": pagination["page_obj"],
        "query": query,
        **pagination,
    })


@login_required
def tshirt_stock_list(request):
    stocks = TshirtStock.objects.select_related("brand").order_by("brand__name", "size")
    query = request.GET.get("q", "").strip()
    if query:
        stocks = stocks.filter(
            models.Q(brand__name__icontains=query)
            | models.Q(size__icontains=query)
        )
    pagination = paginate_queryset(request, stocks)
    return render(request, "inventory/tshirts/stock_list.html", {
        "stocks": pagination["page_obj"],
        "query": query,
        **pagination,
    })


@login_required
def tshirt_allocation_list(request):
    allocations = TshirtAllocation.objects.select_related(
        "employee", "employee_record", "stock", "stock__brand",
        "requested_by", "approved_by", "issued_by"
    ).order_by("-requested_at")
    query = request.GET.get("q", "").strip()
    if query:
        allocations = allocations.filter(
            models.Q(employee_record__employee_id__icontains=query)
            | models.Q(employee_record__full_name__icontains=query)
            | models.Q(employee__employee_id__icontains=query)
            | models.Q(employee__full_name__icontains=query)
            | models.Q(stock__brand__name__icontains=query)
            | models.Q(stock__size__icontains=query)
            | models.Q(status__icontains=query)
            | models.Q(issue_type__icontains=query)
        )
    pagination = paginate_queryset(request, allocations)
    return render(request, "inventory/tshirts/allocation_list.html", {
        "allocations": pagination["page_obj"],
        "query": query,
        **pagination,
    })


@login_required
def book_history(request):
    allocations = BookAllocation.objects.select_related(
        "book", "employee", "employee_record", "allocated_by", "returned_by"
    ).order_by("-allocated_at")
    query = request.GET.get("q", "").strip()
    if query:
        allocations = allocations.filter(
            models.Q(book__asset_id__icontains=query)
            | models.Q(book__name__icontains=query)
            | models.Q(employee_record__employee_id__icontains=query)
            | models.Q(employee_record__full_name__icontains=query)
            | models.Q(employee__employee_id__icontains=query)
            | models.Q(employee__full_name__icontains=query)
        )
    pagination = paginate_queryset(request, allocations)
    return render(request, "inventory/books/history.html", {
        "allocations": pagination["page_obj"],
        "query": query,
        **pagination,
    })


@login_required
def employee_history(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    all_books = BookAllocation.objects.select_related("book", "allocated_by", "returned_by").filter(
        employee_record=employee
    ).order_by("-allocated_at")
    all_tshirts = TshirtAllocation.objects.select_related(
        "stock", "stock__brand", "requested_by", "issued_by", "approved_by"
    ).filter(employee_record=employee).order_by("-requested_at")

    book_query = request.GET.get("book_q", "").strip()
    if book_query:
        all_books = all_books.filter(
            models.Q(book__asset_id__icontains=book_query)
            | models.Q(book__name__icontains=book_query)
            | models.Q(return_note__icontains=book_query)
        )

    tshirt_query = request.GET.get("tshirt_q", "").strip()
    if tshirt_query:
        all_tshirts = all_tshirts.filter(
            models.Q(stock__brand__name__icontains=tshirt_query)
            | models.Q(stock__size__icontains=tshirt_query)
            | models.Q(status__icontains=tshirt_query)
            | models.Q(issue_type__icontains=tshirt_query)
        )

    book_pagination = paginate_queryset(
        request, all_books, page_parameter="book_page", size_parameter="book_page_size"
    )
    tshirt_pagination = paginate_queryset(
        request, all_tshirts, page_parameter="tshirt_page", size_parameter="tshirt_page_size"
    )

    full_book_history = BookAllocation.objects.filter(employee_record=employee)
    full_tshirt_history = TshirtAllocation.objects.filter(employee_record=employee)
    entitlement_rows = [
        {"brand": brand, **free_entitlement(employee, brand)}
        for brand in TshirtBrand.objects.filter(is_active=True).order_by("name")
    ]

    return render(request, "inventory/employees/history.html", {
        "employee": employee,
        "book_history": book_pagination["page_obj"],
        "tshirt_history": tshirt_pagination["page_obj"],
        "book_query": book_query,
        "tshirt_query": tshirt_query,
        "book_pagination": book_pagination,
        "tshirt_pagination": tshirt_pagination,
        "entitlement_rows": entitlement_rows,
        "book_transaction_count": full_book_history.count(),
        "open_books": full_book_history.filter(is_active=True).count(),
        "total_tshirts": sum(
            item.quantity for item in full_tshirt_history.filter(status=TshirtAllocation.Status.ISSUED)
        ),
    })


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_brand_list(request):
    brands = TshirtBrand.objects.prefetch_related("stock_items").order_by("name")
    query = request.GET.get("q", "").strip()
    if query:
        brands = brands.filter(name__icontains=query)
    pagination = paginate_queryset(request, brands)
    return render(request, "inventory/tshirts/brand_list.html", {
        "brands": pagination["page_obj"],
        "query": query,
        **pagination,
    })
