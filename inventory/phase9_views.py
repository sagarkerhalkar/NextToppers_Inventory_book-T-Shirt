import mimetypes
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .enhanced_forms import TshirtStockCorrectionForm
from .forms import (
    BookAllocationAdminEditForm, BookAllocationForm, BookReturnForm, EmployeeRecordForm,
    FreeTshirtIssueForm, PaidTshirtRequestForm, TshirtAllocationAdminEditForm,
)
from .models import Book, BookAllocation, Employee, TshirtAllocation, TshirtStock, User
from .permissions import role_required
from .services import (
    admin_delete_book_allocation, admin_delete_tshirt_allocation,
    admin_edit_book_allocation, admin_edit_tshirt_allocation,
    allocate_book, audit, create_paid_tshirt_request, issue_free_tshirts, return_book,
)


@login_required
def employee_autocomplete(request):
    query = request.GET.get("q", "").strip()
    employees = Employee.objects.filter(is_active=True)
    if query:
        employees = employees.filter(
            models.Q(employee_id__icontains=query)
            | models.Q(full_name__icontains=query)
            | models.Q(mobile_number__icontains=query)
            | models.Q(department__icontains=query)
            | models.Q(designation__icontains=query)
        )
    employees = employees.order_by("employee_id")[:20]
    return JsonResponse({
        "results": [
            {
                "id": employee.pk,
                "text": f"{employee.employee_id} - {employee.full_name}"
                + (f" - {employee.mobile_number}" if employee.mobile_number else ""),
            }
            for employee in employees
        ]
    })


@login_required
def tshirt_stock_autocomplete(request):
    query = request.GET.get("q", "").strip()
    stocks = TshirtStock.objects.select_related("brand").filter(brand__is_active=True)
    if query:
        stocks = stocks.filter(models.Q(brand__name__icontains=query) | models.Q(size__icontains=query))
    stocks = stocks.order_by("brand__name", "size")[:20]
    return JsonResponse({
        "results": [
            {
                "id": stock.pk,
                "text": f"{stock.brand.name} - Size {stock.size} - Available {stock.available_quantity}",
            }
            for stock in stocks
        ]
    })


@login_required
def employee_create(request):
    form = EmployeeRecordForm(request.POST or None, request.FILES or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        audit(
            request.user,
            "EMPLOYEE_CREATED",
            employee,
            f"Created non-login employee {employee.employee_id}",
            metadata={
                "entitlement_start": str(employee.tshirt_entitlement_start_date or ""),
                "entitlement_end": str(employee.tshirt_entitlement_end_date or ""),
            },
        )
        messages.success(request, "Employee record created. No login account was created.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": "Add Employee (No Login)",
        "help_text": "Admin/Super Admin may optionally set a different T-shirt entitlement start and end date for this employee. The dates remain editable.",
    })


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    previous = {
        "employee_id": employee.employee_id,
        "entitlement_start": str(employee.tshirt_entitlement_start_date or ""),
        "entitlement_end": str(employee.tshirt_entitlement_end_date or ""),
    }
    form = EmployeeRecordForm(request.POST or None, request.FILES or None, instance=employee, actor=request.user)
    if request.method == "POST" and form.is_valid():
        updated = form.save()
        audit(
            request.user,
            "EMPLOYEE_EDITED",
            updated,
            f"Edited employee {updated.employee_id}",
            metadata={
                "previous": previous,
                "new_employee_id": updated.employee_id,
                "new_entitlement_start": str(updated.tshirt_entitlement_start_date or ""),
                "new_entitlement_end": str(updated.tshirt_entitlement_end_date or ""),
            },
        )
        messages.success(request, "Employee updated.")
        return redirect("inventory:employee_list")
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": f"Edit Employee {employee.employee_id}",
        "help_text": "The optional T-shirt entitlement period can be corrected whenever the employee policy changes.",
    })


@login_required
def book_allocate(request, pk):
    book = get_object_or_404(Book, pk=pk, is_active=True)
    form = BookAllocationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            allocation = allocate_book(
                book=book,
                employee=form.cleaned_data["employee"],
                actor=request.user,
                allocated_at=form.cleaned_data.get("allocated_at"),
            )
            messages.success(request, f"Book allocated. Recorded date/time: {allocation.allocated_at:%d-%m-%Y %H:%M}.")
            return redirect("inventory:book_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": f"Allocate {book.asset_id}",
        "help_text": "Search Employee ID, name or mobile instead of scrolling. Leave the date blank for now, or enter an earlier date for a past transaction.",
    })


@login_required
def book_return(request, pk):
    allocation = get_object_or_404(BookAllocation.objects.select_related("book"), pk=pk, is_active=True)
    form = BookReturnForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            returned = return_book(
                allocation=allocation,
                condition=form.cleaned_data["return_condition"],
                note=form.cleaned_data["return_note"],
                actor=request.user,
                returned_at=form.cleaned_data.get("returned_at"),
            )
            messages.success(request, f"Book returned. Recorded date/time: {returned.returned_at:%d-%m-%Y %H:%M}.")
            return redirect("inventory:book_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": f"Return {allocation.book.asset_id}",
        "help_text": "A past return date/time is allowed, but it cannot be before the allocation date/time.",
    })


@login_required
def free_tshirt_issue(request):
    form = FreeTshirtIssueForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            allocation = issue_free_tshirts(
                employee=form.cleaned_data["employee"],
                stock=form.cleaned_data["stock"],
                quantity=form.cleaned_data["quantity"],
                actor=request.user,
                issued_at=form.cleaned_data.get("issued_at"),
            )
            messages.success(request, f"Free T-shirt issued. Recorded date/time: {allocation.issued_at:%d-%m-%Y %H:%M}.")
            return redirect("inventory:tshirt_allocation_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": "Issue Free T-shirt",
        "help_text": "Search Employee and T-shirt stock. Past entries are allowed. The employee-specific entitlement period is checked automatically.",
    })


@login_required
def paid_tshirt_request(request):
    form = PaidTshirtRequestForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            create_paid_tshirt_request(actor=request.user, **form.cleaned_data)
            messages.success(request, "Paid T-shirt request saved. Admin/Super Admin can review the uploaded documents before approval.")
            return redirect("inventory:tshirt_allocation_list")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": "Paid T-shirt Request",
        "help_text": "Search Employee and stock. Upload payment and HR approval documents. A past request/entry date may be recorded.",
    })


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def book_allocation_edit(request, pk):
    allocation = get_object_or_404(
        BookAllocation.objects.select_related("book", "employee", "employee_record"),
        pk=pk,
    )
    initial = {
        "employee": allocation.employee_record_id or allocation.employee_id,
        "allocated_at": allocation.allocated_at,
        "allocation_status": (
            BookAllocationAdminEditForm.STATUS_ACTIVE
            if allocation.is_active
            else BookAllocationAdminEditForm.STATUS_RETURNED
        ),
        "returned_at": allocation.returned_at,
        "return_condition": allocation.return_condition,
        "return_note": allocation.return_note,
    }
    form = BookAllocationAdminEditForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            updated = admin_edit_book_allocation(
                allocation=allocation,
                employee=form.cleaned_data["employee"],
                allocated_at=form.cleaned_data["allocated_at"],
                allocation_status=form.cleaned_data["allocation_status"],
                returned_at=form.cleaned_data.get("returned_at"),
                return_condition=form.cleaned_data.get("return_condition") or "",
                return_note=form.cleaned_data.get("return_note") or "",
                actor=request.user,
            )
            messages.success(request, "Book employee transaction updated and inventory status recalculated.")
            return redirect("inventory:employee_history", pk=updated.employee_record_id)
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": f"Edit Book Transaction: {allocation.book.asset_id}",
        "help_text": "Admin correction. Employee, allocation/return dates and return details can be corrected. Inventory status is recalculated automatically.",
    })


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def book_allocation_delete(request, pk):
    allocation = get_object_or_404(
        BookAllocation.objects.select_related("book", "employee", "employee_record"),
        pk=pk,
    )
    employee_pk = allocation.employee_record_id
    if request.method == "POST":
        admin_delete_book_allocation(allocation=allocation, actor=request.user)
        messages.success(request, "Book employee transaction deleted and Book availability recalculated.")
        if employee_pk:
            return redirect("inventory:employee_history", pk=employee_pk)
        return redirect("inventory:book_history")

    return render(request, "inventory/confirm_transaction_delete.html", {
        "transaction_type": "Book",
        "title": "Delete Book Employee Entry",
        "employee": allocation.recipient,
        "item_name": f"{allocation.book.asset_id} - {allocation.book.name}",
        "quantity": None,
        "status": "Currently Allocated" if allocation.is_active else "Returned",
        "transaction_date": allocation.allocated_at,
        "warning": "This deletes only this employee Book transaction. The Book itself is not deleted. Book availability/status will be recalculated automatically.",
        "cancel_url_name": "inventory:employee_history" if employee_pk else "inventory:book_history",
        "cancel_pk": employee_pk,
    })


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_allocation_edit(request, pk):
    allocation = get_object_or_404(
        TshirtAllocation.objects.select_related("stock", "stock__brand", "employee", "employee_record"),
        pk=pk,
    )
    initial = {
        "employee": allocation.employee_record_id or allocation.employee_id,
        "stock": allocation.stock_id,
        "quantity": allocation.quantity,
        "requested_at": allocation.requested_at,
        "issued_at": allocation.issued_at,
    }
    form = TshirtAllocationAdminEditForm(request.POST or None, initial=initial, allocation=allocation)
    if request.method == "POST" and form.is_valid():
        try:
            updated = admin_edit_tshirt_allocation(
                allocation=allocation,
                employee=form.cleaned_data["employee"],
                stock=form.cleaned_data["stock"],
                quantity=form.cleaned_data["quantity"],
                requested_at=form.cleaned_data["requested_at"],
                issued_at=form.cleaned_data.get("issued_at"),
                actor=request.user,
            )
            messages.success(request, "T-shirt employee transaction updated and stock recalculated.")
            return redirect("inventory:employee_history", pk=updated.employee_record_id)
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": f"Edit T-shirt Transaction #{allocation.pk}",
        "help_text": "Admin correction. Employee, T-shirt stock, quantity and dates can be corrected. Issued stock is recalculated automatically.",
    })


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_allocation_delete(request, pk):
    allocation = get_object_or_404(
        TshirtAllocation.objects.select_related("stock", "stock__brand", "employee", "employee_record"),
        pk=pk,
    )
    employee_pk = allocation.employee_record_id
    if request.method == "POST":
        admin_delete_tshirt_allocation(allocation=allocation, actor=request.user)
        messages.success(request, "T-shirt employee transaction deleted and stock restored automatically.")
        if employee_pk:
            return redirect("inventory:employee_history", pk=employee_pk)
        return redirect("inventory:tshirt_allocation_list")

    return render(request, "inventory/confirm_transaction_delete.html", {
        "transaction_type": "T-shirt",
        "title": "Delete T-shirt Employee Entry",
        "employee": allocation.recipient,
        "item_name": f"{allocation.stock.brand.name} / Size {allocation.stock.size}",
        "quantity": allocation.quantity,
        "status": allocation.get_status_display(),
        "transaction_date": allocation.issued_at or allocation.requested_at,
        "warning": "This deletes only this employee T-shirt transaction. If it was already issued, the issued quantity will be restored to available stock automatically.",
        "cancel_url_name": "inventory:employee_history" if employee_pk else "inventory:tshirt_allocation_list",
        "cancel_pk": employee_pk,
    })




@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
@transaction.atomic
def employee_book_transactions_bulk_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method != "POST":
        return redirect("inventory:employee_history", pk=employee.pk)

    selected_ids = request.POST.getlist("book_transaction_ids")
    if not selected_ids:
        messages.error(request, "Select at least one Book entry to delete.")
        return redirect("inventory:employee_history", pk=employee.pk)

    allocations = list(
        BookAllocation.objects.select_for_update()
        .select_related("book", "employee", "employee_record")
        .filter(pk__in=selected_ids, employee_record=employee)
        .order_by("pk")
    )
    if not allocations:
        messages.error(request, "No matching Book entries were found.")
        return redirect("inventory:employee_history", pk=employee.pk)

    deleted = 0
    for allocation in allocations:
        admin_delete_book_allocation(allocation=allocation, actor=request.user)
        deleted += 1

    messages.success(
        request,
        f"{deleted} Book entr{'y' if deleted == 1 else 'ies'} deleted. The employee was not deleted.",
    )
    return redirect("inventory:employee_history", pk=employee.pk)


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
@transaction.atomic
def employee_tshirt_transactions_bulk_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method != "POST":
        return redirect("inventory:employee_history", pk=employee.pk)

    selected_ids = request.POST.getlist("tshirt_transaction_ids")
    if not selected_ids:
        messages.error(request, "Select at least one T-shirt entry to delete.")
        return redirect("inventory:employee_history", pk=employee.pk)

    allocations = list(
        TshirtAllocation.objects.select_for_update()
        .select_related("stock", "stock__brand", "employee", "employee_record")
        .filter(pk__in=selected_ids, employee_record=employee)
        .order_by("pk")
    )
    if not allocations:
        messages.error(request, "No matching T-shirt entries were found.")
        return redirect("inventory:employee_history", pk=employee.pk)

    deleted = 0
    for allocation in allocations:
        admin_delete_tshirt_allocation(allocation=allocation, actor=request.user)
        deleted += 1

    messages.success(
        request,
        f"{deleted} T-shirt entr{'y' if deleted == 1 else 'ies'} deleted. Issued stock was restored automatically. The employee was not deleted.",
    )
    return redirect("inventory:employee_history", pk=employee.pk)




@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_stock_correct(request, pk):
    stock = get_object_or_404(TshirtStock.objects.select_related("brand"), pk=pk)
    form = TshirtStockCorrectionForm(request.POST or None, stock=stock)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked = TshirtStock.objects.select_for_update().select_related("brand").get(pk=stock.pk)
            old_quantity = locked.available_quantity
            new_quantity = form.cleaned_data["available_quantity"]
            reason = form.cleaned_data["correction_reason"]
            locked.available_quantity = new_quantity
            locked.save(update_fields=["available_quantity", "updated_at"])
            audit(
                request.user,
                "TSHIRT_AVAILABLE_STOCK_CORRECTED",
                locked,
                f"Corrected {locked.brand.name}/{locked.size} available stock from {old_quantity} to {new_quantity}. Reason: {reason}",
                metadata={"old_available": old_quantity, "new_available": new_quantity, "reason": reason},
            )
        messages.success(request, "Available T-shirt stock corrected and recorded in the audit log.")
        return redirect("inventory:tshirt_stock_list")
    return render(request, "inventory/generic_form.html", {
        "form": form,
        "title": f"Correct Available Stock: {stock.brand.name} / {stock.size}",
        "help_text": f"Current available quantity: {stock.available_quantity}. This Admin correction does not erase issue or purchase history.",
    })


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def paid_tshirt_review(request, pk):
    allocation = get_object_or_404(
        TshirtAllocation.objects.select_related(
            "employee", "employee_record", "stock", "stock__brand", "requested_by", "approved_by", "issued_by"
        ),
        pk=pk,
        issue_type=TshirtAllocation.IssueType.PAID,
    )
    return render(request, "inventory/tshirts/paid_review.html", {"allocation": allocation})


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def book_detail(request, pk):
    book = get_object_or_404(Book.objects.prefetch_related("allocations"), pk=pk)
    return render(request, "inventory/books/detail.html", {"book": book})


def _protected_file_response(field_file, fallback_name):
    if not field_file:
        raise Http404("Document is not available.")
    try:
        handle = field_file.open("rb")
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise Http404("Document file is not available.") from exc
    filename = Path(field_file.name).name or fallback_name
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    response = FileResponse(handle, content_type=content_type)
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def book_document(request, pk, document_type):
    book = get_object_or_404(Book, pk=pk)
    fields = {"photo": book.book_photo, "bill": book.bill_photo}
    if document_type not in fields:
        raise Http404("Unknown Book document.")
    audit(request.user, "BOOK_DOCUMENT_VIEWED", book, f"Viewed {document_type} for {book.asset_id}")
    return _protected_file_response(fields[document_type], f"{book.asset_id}_{document_type}")


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def paid_tshirt_document(request, pk, document_type):
    allocation = get_object_or_404(TshirtAllocation, pk=pk, issue_type=TshirtAllocation.IssueType.PAID)
    fields = {"payment": allocation.payment_proof, "hr": allocation.hr_approval_proof}
    if document_type not in fields:
        raise Http404("Unknown paid T-shirt document.")
    audit(request.user, "PAID_TSHIRT_DOCUMENT_VIEWED", allocation, f"Viewed {document_type} document for paid request {allocation.pk}")
    return _protected_file_response(fields[document_type], f"paid_request_{allocation.pk}_{document_type}")
