from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AuditLog, Book, BookAllocation, BrandingSettings, NotificationLog, TshirtAllocation, TshirtBrand, TshirtPurchase, TshirtStock, User


@admin.register(User)
class EmployeeAdmin(UserAdmin):
    ordering = ("employee_id",)
    list_display = ("employee_id", "full_name", "mobile_number", "role", "is_active")
    search_fields = ("employee_id", "full_name", "mobile_number")
    fieldsets = (
        (None, {"fields": ("employee_id", "password")}),
        ("Employee", {"fields": ("full_name", "mobile_number", "email", "department", "designation", "joining_date", "office_location", "profile_picture", "default_tshirt_size")}),
        ("Access", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions", "must_change_password")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("employee_id", "full_name", "mobile_number", "role", "password1", "password2")}),)


for model in [AuditLog, Book, BookAllocation, BrandingSettings, NotificationLog, TshirtAllocation, TshirtBrand, TshirtPurchase, TshirtStock]:
    admin.site.register(model)
