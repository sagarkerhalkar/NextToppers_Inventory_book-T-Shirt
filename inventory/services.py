import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import AuditLog, Book, BookAllocation, Employee, NotificationLog, TshirtAllocation, TshirtPurchase, TshirtStock


def audit(actor, action, entity, description="", metadata=None):
    AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        entity_type=entity.__class__.__name__,
        entity_id=str(getattr(entity, "pk", "")),
        description=description,
        metadata=metadata or {},
    )


def _employee_kwargs(employee):
    return {"employee_record": employee} if isinstance(employee, Employee) else {"employee": employee}


@transaction.atomic
def allocate_book(*, book, employee, actor):
    locked = Book.objects.select_for_update().get(pk=book.pk)
    if locked.status != Book.Status.IN_LIBRARY or locked.condition in {Book.Condition.LOST, Book.Condition.DAMAGED}:
        raise ValueError("This Book is not available for allocation.")
    allocation = BookAllocation.objects.create(book=locked, allocated_by=actor, **_employee_kwargs(employee))
    locked.status = Book.Status.ALLOCATED
    locked.save(update_fields=["status", "updated_at"])
    audit(actor, "BOOK_ALLOCATED", allocation, f"{locked.asset_id} allocated to {employee.employee_id}")
    notify_allocation(employee, f"Book {locked.asset_id} - {locked.name} has been allocated to {employee.full_name}.")
    return allocation


@transaction.atomic
def return_book(*, allocation, condition, note, actor):
    locked = BookAllocation.objects.select_for_update().select_related("book", "employee", "employee_record").get(pk=allocation.pk)
    if not locked.is_active:
        raise ValueError("This Book allocation is already closed.")
    if not note.strip():
        raise ValueError("Return note is mandatory.")
    now = timezone.now()
    locked.is_active = False
    locked.returned_at = now
    locked.return_condition = condition
    locked.return_note = note.strip()
    locked.returned_by = actor
    locked.save()
    book = locked.book
    book.condition = condition
    book.status = {Book.Condition.LOST: Book.Status.LOST, Book.Condition.DAMAGED: Book.Status.DAMAGED}.get(condition, Book.Status.IN_LIBRARY)
    book.save(update_fields=["condition", "status", "updated_at"])
    recipient = locked.recipient
    audit(actor, "BOOK_RETURNED", locked, f"{book.asset_id} returned by {recipient.employee_id}")
    return locked


@transaction.atomic
def add_tshirt_purchase(*, stock, quantity, actor, **purchase_fields):
    locked = TshirtStock.objects.select_for_update().get(pk=stock.pk)
    purchase = TshirtPurchase.objects.create(stock=locked, quantity=quantity, created_by=actor, **purchase_fields)
    locked.available_quantity += quantity
    locked.save(update_fields=["available_quantity", "updated_at"])
    audit(actor, "TSHIRT_PURCHASE_ADDED", purchase, f"Added {quantity} units to {locked}")
    return purchase


def free_entitlement(employee, brand):
    used = TshirtAllocation.rolling_free_used(employee, brand)
    allowance = brand.free_quantity_rolling_12_months
    return {"allowance": allowance, "used": used, "remaining": max(allowance - used, 0)}


@transaction.atomic
def issue_free_tshirts(*, employee, stock, quantity, actor):
    locked = TshirtStock.objects.select_for_update().select_related("brand").get(pk=stock.pk)
    summary = free_entitlement(employee, locked.brand)
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")
    if quantity > summary["remaining"]:
        raise ValueError("Free allowance is not sufficient. Create a paid request for the extra quantity.")
    if locked.available_quantity < quantity:
        raise ValueError("T-shirt stock is insufficient.")
    allocation = TshirtAllocation.objects.create(
        stock=locked,
        quantity=quantity,
        issue_type=TshirtAllocation.IssueType.FREE,
        status=TshirtAllocation.Status.ISSUED,
        requested_by=actor,
        issued_by=actor,
        issued_at=timezone.now(),
        **_employee_kwargs(employee),
    )
    locked.available_quantity -= quantity
    locked.allocated_quantity += quantity
    locked.save(update_fields=["available_quantity", "allocated_quantity", "updated_at"])
    audit(actor, "FREE_TSHIRT_ISSUED", allocation, f"Issued {quantity} free {locked.brand.name} T-shirt(s) to {employee.employee_id}")
    notify_allocation(employee, f"{quantity} {locked.brand.name} T-shirt(s), size {locked.size}, have been issued to {employee.full_name}.")
    return allocation


def create_paid_tshirt_request(*, employee, stock, quantity, actor, payment_amount, payment_date, payment_proof, hr_approval_proof):
    if not payment_proof or not hr_approval_proof or not payment_amount or not payment_date:
        raise ValueError("Payment amount, payment date, payment proof and HR approval proof are mandatory.")
    allocation = TshirtAllocation.objects.create(
        stock=stock,
        quantity=quantity,
        issue_type=TshirtAllocation.IssueType.PAID,
        status=TshirtAllocation.Status.PENDING,
        requested_by=actor,
        payment_amount=payment_amount,
        payment_date=payment_date,
        payment_proof=payment_proof,
        hr_approval_proof=hr_approval_proof,
        **_employee_kwargs(employee),
    )
    audit(actor, "PAID_TSHIRT_REQUESTED", allocation, f"Paid T-shirt request for {employee.employee_id}")
    return allocation


@transaction.atomic
def approve_paid_tshirt_request(*, allocation, actor):
    if actor.role not in {actor.Role.ADMIN, actor.Role.SUPER_ADMIN}:
        raise PermissionError("Only Admin or Super Admin can approve paid T-shirt requests.")
    locked = TshirtAllocation.objects.select_for_update().select_related("stock", "stock__brand", "employee", "employee_record").get(pk=allocation.pk)
    if locked.status != TshirtAllocation.Status.PENDING or locked.issue_type != TshirtAllocation.IssueType.PAID:
        raise ValueError("This request is not pending approval.")
    if not locked.payment_proof or not locked.hr_approval_proof or not locked.payment_amount or not locked.payment_date:
        raise ValueError("Complete payment and HR approval evidence is required.")
    stock = TshirtStock.objects.select_for_update().get(pk=locked.stock_id)
    if stock.available_quantity < locked.quantity:
        raise ValueError("T-shirt stock is insufficient.")
    now = timezone.now()
    locked.status = TshirtAllocation.Status.ISSUED
    locked.approved_by = actor
    locked.approved_at = now
    locked.issued_by = actor
    locked.issued_at = now
    locked.save()
    stock.available_quantity -= locked.quantity
    stock.allocated_quantity += locked.quantity
    stock.save(update_fields=["available_quantity", "allocated_quantity", "updated_at"])
    recipient = locked.recipient
    audit(actor, "PAID_TSHIRT_APPROVED", locked, f"Approved paid T-shirt request for {recipient.employee_id}")
    notify_allocation(recipient, f"Paid T-shirt request for {stock.brand.name}, size {stock.size}, has been approved and issued.")
    return locked


def reject_paid_tshirt_request(*, allocation, reason, actor):
    if actor.role not in {actor.Role.ADMIN, actor.Role.SUPER_ADMIN}:
        raise PermissionError("Only Admin or Super Admin can reject paid T-shirt requests.")
    if not reason.strip():
        raise ValueError("Rejection reason is mandatory.")
    allocation.status = TshirtAllocation.Status.REJECTED
    allocation.approved_by = actor
    allocation.approved_at = timezone.now()
    allocation.rejection_reason = reason.strip()
    allocation.save(update_fields=["status", "approved_by", "approved_at", "rejection_reason", "updated_at"])
    audit(actor, "PAID_TSHIRT_REJECTED", allocation, reason.strip())
    return allocation


def notify_allocation(employee, message):
    log_kwargs = {"employee_record": employee} if isinstance(employee, Employee) else {"recipient": employee}
    NotificationLog.objects.create(channel=NotificationLog.Channel.IN_APP, message=message, status=NotificationLog.Status.SENT, sent_at=timezone.now(), **log_kwargs)
    if employee.email:
        log = NotificationLog.objects.create(channel=NotificationLog.Channel.EMAIL, subject="Next Toppers Inventory Update", message=message, **log_kwargs)
        try:
            send_mail(log.subject, message, settings.DEFAULT_FROM_EMAIL, [employee.email], fail_silently=False)
            log.status = NotificationLog.Status.SENT
            log.sent_at = timezone.now()
        except Exception as exc:
            log.status = NotificationLog.Status.FAILED
            log.error_message = str(exc)
        log.save()
    webhook = settings.GOOGLE_CHAT_WEBHOOK_URL
    if webhook:
        log = NotificationLog.objects.create(channel=NotificationLog.Channel.GOOGLE_CHAT, message=message, **log_kwargs)
        try:
            response = requests.post(webhook, json={"text": message}, timeout=10)
            response.raise_for_status()
            log.status = NotificationLog.Status.SENT
            log.sent_at = timezone.now()
        except Exception as exc:
            log.status = NotificationLog.Status.FAILED
            log.error_message = str(exc)
        log.save()
