from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, Book, BookAllocation, BrandingSettings, Employee, NotificationLog, TshirtAllocation, TshirtBrand, TshirtPurchase, TshirtStock, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ("employee_id",)
    list_display = ("employee_id", "full_name", "role", "mobile_number", "is_active")
    search_fields = ("employee_id", "full_name", "mobile_number")
    fieldsets = (
        (None, {"fields": ("employee_id", "password")}),
        ("Login user", {"fields": ("full_name", "mobile_number", "email", "role", "profile_picture")}),
        ("Work", {"fields": ("department", "designation", "office_location")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Security", {"fields": ("must_change_password", "last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("employee_id", "full_name", "mobile_number", "role", "password1", "password2")}),)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "mobile_number", "default_tshirt_size", "is_active")
    search_fields = ("employee_id", "full_name", "mobile_number")
    list_filter = ("is_active", "default_tshirt_size", "department")


admin.site.register(Book)
admin.site.register(BookAllocation)
admin.site.register(TshirtBrand)
admin.site.register(TshirtStock)
admin.site.register(TshirtPurchase)
admin.site.register(TshirtAllocation)
admin.site.register(BrandingSettings)
admin.site.register(NotificationLog)
admin.site.register(AuditLog)
