from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inventory.models import Book, BookAllocation, Employee, TshirtAllocation, TshirtBrand, TshirtStock, User


class PeriodicReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "NXTTP0001", "Admin", "+919876543210", "StrongPass123!", role=User.Role.ADMIN
        )
        self.employee = Employee.objects.create(
            employee_id="NXTTP0002", full_name="Employee", mobile_number="+919876543211"
        )
        self.book = Book.objects.create(name="Mathematics", created_by=self.user)
        BookAllocation.objects.create(book=self.book, employee_record=self.employee, allocated_by=self.user)
        brand = TshirtBrand.objects.create(name="Next Toppers", free_quantity_rolling_12_months=5)
        stock = TshirtStock.objects.create(brand=brand, size="L", available_quantity=10)
        TshirtAllocation.objects.create(
            employee_record=self.employee,
            stock=stock,
            quantity=1,
            issue_type=TshirtAllocation.IssueType.FREE,
            status=TshirtAllocation.Status.ISSUED,
            requested_by=self.user,
            issued_by=self.user,
            issued_at=timezone.now(),
        )
        self.client.force_login(self.user)

    def test_combined_month_excel_download(self):
        response = self.client.get(reverse("inventory:download_activity_report"), {
            "report_type": "combined", "period": "month", "format": "xlsx"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])

    def test_book_custom_pdf_download(self):
        today = timezone.localdate()
        response = self.client.get(reverse("inventory:download_activity_report"), {
            "report_type": "book",
            "period": "custom",
            "format": "pdf",
            "start_date": (today - timedelta(days=1)).isoformat(),
            "end_date": today.isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_invalid_custom_range_is_rejected(self):
        response = self.client.get(reverse("inventory:download_activity_report"), {
            "report_type": "combined", "period": "custom", "format": "xlsx"
        })
        self.assertEqual(response.status_code, 400)
