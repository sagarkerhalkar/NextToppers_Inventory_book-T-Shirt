from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .managers import EmployeeManager
from .validators import validate_book_asset_id, validate_employee_id, validate_indian_mobile


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        ADMIN = "ADMIN", "Admin"
        STAFF = "STAFF", "Data Entry User"

    class TshirtSize(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"
        XXXL = "XXXL", "XXXL"

    username = None
    employee_id = models.CharField(max_length=9, unique=True, validators=[validate_employee_id])
    full_name = models.CharField(max_length=180)
    mobile_number = models.CharField(max_length=13, unique=True, validators=[validate_indian_mobile])
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    department = models.CharField(max_length=120, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    office_location = models.CharField(max_length=160, blank=True)
    profile_picture = models.ImageField(upload_to="login_users/", blank=True)
    default_tshirt_size = models.CharField(max_length=5, choices=TshirtSize.choices, default=TshirtSize.L)
    must_change_password = models.BooleanField(default=False)

    USERNAME_FIELD = "employee_id"
    REQUIRED_FIELDS = ["full_name", "mobile_number"]
    objects = EmployeeManager()

    def save(self, *args, **kwargs):
        self.employee_id = (self.employee_id or "").upper().strip()
        self.mobile_number = (self.mobile_number or "").strip()
        self.full_name = (self.full_name or "").strip()
        if self.pk:
            old_id = type(self).objects.filter(pk=self.pk).values_list("employee_id", flat=True).first()
            if old_id and old_id != self.employee_id:
                raise ValidationError("Login User ID cannot be changed after the account is created.")
        if self.role in {self.Role.ADMIN, self.Role.SUPER_ADMIN}:
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"

    @property
    def is_admin_role(self):
        return self.role in {self.Role.ADMIN, self.Role.SUPER_ADMIN}


class Employee(TimeStampedModel):
    """Non-login employee master used for Book and T-shirt transactions."""

    employee_id = models.CharField(max_length=9, unique=True, validators=[validate_employee_id])
    full_name = models.CharField(max_length=180)
    mobile_number = models.CharField(max_length=13, unique=True, validators=[validate_indian_mobile])
    email = models.EmailField(blank=True)
    department = models.CharField(max_length=120, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    office_location = models.CharField(max_length=160, blank=True)
    profile_picture = models.ImageField(upload_to="employees/", blank=True)
    default_tshirt_size = models.CharField(max_length=5, choices=User.TshirtSize.choices, default=User.TshirtSize.L)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["employee_id"]
        indexes = [models.Index(fields=["full_name", "mobile_number"])]

    def save(self, *args, **kwargs):
        self.employee_id = (self.employee_id or "").upper().strip()
        self.mobile_number = (self.mobile_number or "").strip()
        self.full_name = (self.full_name or "").strip()
        if self.pk:
            old_id = type(self).objects.filter(pk=self.pk).values_list("employee_id", flat=True).first()
            if old_id and old_id != self.employee_id:
                raise ValidationError("Employee ID cannot be changed after the employee record is created.")
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_actions")
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class BrandingSettings(TimeStampedModel):
    organization_name = models.CharField(max_length=180, default="Next Toppers")
    app_logo = models.ImageField(upload_to="branding/", blank=True)
    login_background = models.ImageField(upload_to="branding/", blank=True)
    home_image = models.ImageField(upload_to="branding/", blank=True)
    organization_picture = models.ImageField(upload_to="branding/", blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and BrandingSettings.objects.exists():
            self.pk = BrandingSettings.objects.first().pk
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Book(TimeStampedModel):
    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        GOOD = "GOOD", "Good"
        DAMAGED = "DAMAGED", "Damaged"
        LOST = "LOST", "Lost"

    class Status(models.TextChoices):
        IN_LIBRARY = "IN_LIBRARY", "In Library"
        ALLOCATED = "ALLOCATED", "Allocated"
        DAMAGED = "DAMAGED", "Damaged"
        LOST = "LOST", "Lost"

    asset_id = models.CharField(max_length=10, unique=True, blank=True, validators=[validate_book_asset_id])
    name = models.CharField(max_length=240)
    class_name = models.CharField(max_length=80, blank=True)
    stream_name = models.CharField(max_length=100, blank=True)
    isbn = models.CharField(max_length=32, blank=True, db_index=True)
    purchase_date = models.DateField(null=True, blank=True)
    bill_number = models.CharField(max_length=100, blank=True)
    bill_photo = models.ImageField(upload_to="book_bills/", blank=True)
    book_photo = models.ImageField(upload_to="books/", blank=True)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GOOD)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_LIBRARY)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="books_created")

    class Meta:
        ordering = ["asset_id"]
        indexes = [models.Index(fields=["name", "class_name", "stream_name"])]

    def save(self, *args, **kwargs):
        if self.pk:
            old_asset = type(self).objects.filter(pk=self.pk).values_list("asset_id", flat=True).first()
            if old_asset and self.asset_id and old_asset != self.asset_id:
                raise ValidationError("Book Asset ID cannot be changed.")
        if self.condition == self.Condition.LOST:
            self.status = self.Status.LOST
        elif self.condition == self.Condition.DAMAGED and self.status != self.Status.ALLOCATED:
            self.status = self.Status.DAMAGED
        super().save(*args, **kwargs)
        if not self.asset_id:
            generated = f"BOOK{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(asset_id=generated)
            self.asset_id = generated

    def delete(self, *args, **kwargs):
        if self.condition in {self.Condition.DAMAGED, self.Condition.LOST} or self.allocations.exists():
            raise ValidationError("Books with Damaged/Lost condition or allocation history cannot be permanently deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.asset_id or 'NEW'} - {self.name}"


class BookAllocation(TimeStampedModel):
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="allocations")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="legacy_book_allocations")
    employee_record = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.PROTECT, related_name="book_allocations")
    allocated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="book_allocations_made")
    allocated_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    return_condition = models.CharField(max_length=20, choices=Book.Condition.choices, blank=True)
    return_note = models.TextField(blank=True)
    returned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="book_returns_processed")

    class Meta:
        ordering = ["-allocated_at"]
        constraints = [models.UniqueConstraint(fields=["book"], condition=Q(is_active=True), name="one_active_allocation_per_book")]

    def clean(self):
        if not self.employee_record_id and not self.employee_id:
            raise ValidationError("An employee is required for Book allocation.")

    @property
    def recipient(self):
        return self.employee_record or self.employee


class TshirtBrand(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    free_quantity_rolling_12_months = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TshirtStock(TimeStampedModel):
    brand = models.ForeignKey(TshirtBrand, on_delete=models.PROTECT, related_name="stock_items")
    size = models.CharField(max_length=5, choices=User.TshirtSize.choices)
    available_quantity = models.PositiveIntegerField(default=0)
    allocated_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["brand", "size"], name="unique_brand_size_stock")]
        ordering = ["brand__name", "size"]

    @property
    def is_low_stock(self):
        return self.available_quantity <= self.low_stock_threshold

    def __str__(self):
        return f"{self.brand} / {self.size}"


class TshirtPurchase(TimeStampedModel):
    stock = models.ForeignKey(TshirtStock, on_delete=models.PROTECT, related_name="purchases")
    purchase_date = models.DateField(default=timezone.localdate)
    vendor = models.CharField(max_length=180, blank=True)
    bill_number = models.CharField(max_length=100, blank=True)
    bill_photo = models.ImageField(upload_to="tshirt_bills/", blank=True)
    quantity = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="tshirt_purchases_created")


class TshirtAllocation(TimeStampedModel):
    class IssueType(models.TextChoices):
        FREE = "FREE", "Free"
        PAID = "PAID", "Paid"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        ISSUED = "ISSUED", "Issued"

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="legacy_tshirt_allocations")
    employee_record = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.PROTECT, related_name="tshirt_allocations")
    stock = models.ForeignKey(TshirtStock, on_delete=models.PROTECT, related_name="allocations")
    quantity = models.PositiveIntegerField(default=1)
    issue_type = models.CharField(max_length=10, choices=IssueType.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="tshirt_requests_created")
    requested_at = models.DateTimeField(default=timezone.now)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="tshirt_requests_decided")
    approved_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="tshirts_issued")
    issued_at = models.DateTimeField(null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payment_proof = models.FileField(upload_to="payment_proofs/", blank=True)
    hr_approval_proof = models.FileField(upload_to="hr_approvals/", blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def clean(self):
        if not self.employee_record_id and not self.employee_id:
            raise ValidationError("An employee is required for T-shirt allocation.")

    @property
    def recipient(self):
        return self.employee_record or self.employee

    @classmethod
    def rolling_free_used(cls, employee, brand, as_of=None):
        as_of = as_of or timezone.now()
        start = as_of - timedelta(days=365)
        filters = {
            "stock__brand": brand,
            "issue_type": cls.IssueType.FREE,
            "status": cls.Status.ISSUED,
            "issued_at__gte": start,
            "issued_at__lte": as_of,
        }
        if isinstance(employee, Employee):
            filters["employee_record"] = employee
        else:
            filters["employee"] = employee
        return cls.objects.filter(**filters).aggregate(total=models.Sum("quantity"))["total"] or 0


class NotificationLog(models.Model):
    class Channel(models.TextChoices):
        IN_APP = "IN_APP", "In-app"
        EMAIL = "EMAIL", "Email"
        GOOGLE_CHAT = "GOOGLE_CHAT", "Google Chat"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    employee_record = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL, related_name="notification_logs")
    channel = models.CharField(max_length=20, choices=Channel.choices)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
