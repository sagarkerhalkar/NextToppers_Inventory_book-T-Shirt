import re

from django.test import Client, TestCase

from inventory.models import AuditLog, Book, BookAllocation, Employee, TshirtBrand, TshirtStock, User


class InternalNullOriginPostFlowTests(TestCase):
    public_host = "156.156.40.51:3458"

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            employee_id="NXTTP9801",
            full_name="Null Origin Test Admin",
            mobile_number="+919876509801",
            password="Test1234",
            role=User.Role.SUPER_ADMIN,
            is_active=True,
            must_change_password=False,
        )
        cls.employee = Employee.objects.create(
            employee_id="NXTTP9802",
            full_name="Null Origin Employee",
            mobile_number="+919876509802",
            is_active=True,
        )
        cls.book = Book.objects.create(
            name="Null Origin Test Book",
            condition=Book.Condition.GOOD,
            status=Book.Status.IN_LIBRARY,
            is_active=True,
            created_by=cls.admin,
        )
        cls.brand = TshirtBrand.objects.create(name="Null Origin Brand", is_active=True)
        cls.stock = TshirtStock.objects.create(
            brand=cls.brand,
            size=User.TshirtSize.L,
            available_quantity=10,
            allocated_quantity=0,
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.admin)

    def _csrf_token(self, path):
        response = self.client.get(path, HTTP_HOST=self.public_host)
        self.assertEqual(response.status_code, 200)
        match = re.search(rb'name="csrfmiddlewaretoken" value="([^"]+)"', response.content)
        self.assertIsNotNone(match, f"No CSRF token rendered by {path}")
        return match.group(1).decode("ascii")

    def test_book_allocation_accepts_real_browser_null_origin_with_valid_token(self):
        path = f"/books/{self.book.pk}/allocate/"
        token = self._csrf_token(path)
        response = self.client.post(
            path,
            {
                "csrfmiddlewaretoken": token,
                "employee": str(self.employee.pk),
                "allocated_at": "",
            },
            HTTP_HOST=self.public_host,
            HTTP_ORIGIN="null",
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Book allocated.")
        allocation = BookAllocation.objects.get(book=self.book, is_active=True)
        self.assertEqual(allocation.employee_record, self.employee)

    def test_tshirt_stock_correction_accepts_null_origin_and_writes_audit(self):
        path = f"/tshirts/stock/{self.stock.pk}/correct/"
        token = self._csrf_token(path)
        response = self.client.post(
            path,
            {
                "csrfmiddlewaretoken": token,
                "available_quantity": "17",
                "correction_reason": "Verified physical count",
            },
            HTTP_HOST=self.public_host,
            HTTP_ORIGIN="null",
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available T-shirt stock corrected")
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.available_quantity, 17)
        self.assertTrue(
            AuditLog.objects.filter(
                action="TSHIRT_AVAILABLE_STOCK_CORRECTED",
                entity_id=str(self.stock.pk),
            ).exists()
        )

    def test_null_origin_still_requires_valid_csrf_token(self):
        path = f"/books/{self.book.pk}/allocate/"
        response = self.client.post(
            path,
            {"employee": str(self.employee.pk), "allocated_at": ""},
            HTTP_HOST=self.public_host,
            HTTP_ORIGIN="null",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(BookAllocation.objects.filter(book=self.book).exists())

    def test_null_origin_is_not_normalized_for_unapproved_host(self):
        path = f"/books/{self.book.pk}/allocate/"
        response = self.client.post(
            path,
            {"employee": str(self.employee.pk), "allocated_at": ""},
            HTTP_HOST="evil.example:3458",
            HTTP_ORIGIN="null",
        )
        self.assertEqual(response.status_code, 400)
