from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from inventory.models import Book, BookAllocation, Employee, TshirtAllocation, TshirtBrand, TshirtStock, User
from inventory.services import (
    admin_delete_book_allocation,
    admin_delete_tshirt_allocation,
    admin_edit_book_allocation,
    admin_edit_tshirt_allocation,
)


class AdminEmployeeTransactionCorrectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            employee_id="NXTTP9601",
            full_name="Transaction Admin",
            mobile_number="+919876509601",
            password="Test1234",
            role=User.Role.ADMIN,
            is_active=True,
            must_change_password=False,
        )
        cls.staff = User.objects.create_user(
            employee_id="NXTTP9602",
            full_name="Transaction Staff",
            mobile_number="+919876509602",
            password="Test1234",
            role=User.Role.STAFF,
            is_active=True,
            must_change_password=False,
        )
        cls.employee_a = Employee.objects.create(
            employee_id="NXTTP9603",
            full_name="Employee A",
            mobile_number="+919876509603",
            is_active=True,
        )
        cls.employee_b = Employee.objects.create(
            employee_id="NXTTP9604",
            full_name="Employee B",
            mobile_number="+919876509604",
            is_active=True,
        )
        cls.brand = TshirtBrand.objects.create(
            name="Transaction Brand",
            free_quantity_rolling_12_months=10,
            is_active=True,
        )

    def setUp(self):
        self.book = Book.objects.create(
            asset_id="TRXBOOK1",
            name="Transaction Book",
            condition=Book.Condition.GOOD,
            status=Book.Status.ALLOCATED,
            created_by=self.admin,
        )
        self.book_allocation = BookAllocation.objects.create(
            book=self.book,
            employee_record=self.employee_a,
            allocated_by=self.admin,
            allocated_at=timezone.now(),
            is_active=True,
        )
        self.stock_a = TshirtStock.objects.create(
            brand=self.brand,
            size=User.TshirtSize.L,
            available_quantity=8,
            allocated_quantity=2,
        )
        self.stock_b = TshirtStock.objects.create(
            brand=self.brand,
            size=User.TshirtSize.XL,
            available_quantity=20,
            allocated_quantity=0,
        )
        self.tshirt_allocation = TshirtAllocation.objects.create(
            employee_record=self.employee_a,
            stock=self.stock_a,
            quantity=2,
            issue_type=TshirtAllocation.IssueType.FREE,
            status=TshirtAllocation.Status.ISSUED,
            requested_by=self.admin,
            requested_at=timezone.now(),
            issued_by=self.admin,
            issued_at=timezone.now(),
        )

    def test_admin_can_edit_active_book_employee_transaction(self):
        updated = admin_edit_book_allocation(
            allocation=self.book_allocation,
            employee=self.employee_b,
            allocated_at=timezone.now(),
            allocation_status="ACTIVE",
            returned_at=None,
            return_condition="",
            return_note="",
            actor=self.admin,
        )
        updated.refresh_from_db()
        self.book.refresh_from_db()
        self.assertEqual(updated.employee_record, self.employee_b)
        self.assertTrue(updated.is_active)
        self.assertEqual(self.book.status, Book.Status.ALLOCATED)

    def test_deleting_active_book_transaction_returns_book_to_inventory(self):
        admin_delete_book_allocation(allocation=self.book_allocation, actor=self.admin)
        self.book.refresh_from_db()
        self.assertFalse(BookAllocation.objects.filter(pk=self.book_allocation.pk).exists())
        self.assertEqual(self.book.status, Book.Status.IN_LIBRARY)

    def test_editing_issued_tshirt_transaction_moves_stock_and_employee(self):
        updated = admin_edit_tshirt_allocation(
            allocation=self.tshirt_allocation,
            employee=self.employee_b,
            stock=self.stock_b,
            quantity=3,
            requested_at=timezone.now(),
            issued_at=timezone.now(),
            actor=self.admin,
        )
        updated.refresh_from_db()
        self.stock_a.refresh_from_db()
        self.stock_b.refresh_from_db()
        self.assertEqual(updated.employee_record, self.employee_b)
        self.assertEqual(updated.stock, self.stock_b)
        self.assertEqual(updated.quantity, 3)
        self.assertEqual(self.stock_a.available_quantity, 10)
        self.assertEqual(self.stock_a.allocated_quantity, 0)
        self.assertEqual(self.stock_b.available_quantity, 17)
        self.assertEqual(self.stock_b.allocated_quantity, 3)

    def test_deleting_issued_tshirt_transaction_restores_stock(self):
        admin_delete_tshirt_allocation(allocation=self.tshirt_allocation, actor=self.admin)
        self.stock_a.refresh_from_db()
        self.assertFalse(TshirtAllocation.objects.filter(pk=self.tshirt_allocation.pk).exists())
        self.assertEqual(self.stock_a.available_quantity, 10)
        self.assertEqual(self.stock_a.allocated_quantity, 0)

    def test_staff_can_open_book_transaction_edit(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("inventory:book_allocation_edit", args=[self.book_allocation.pk]))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_open_tshirt_transaction_edit(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("inventory:tshirt_allocation_edit", args=[self.tshirt_allocation.pk]))
        self.assertEqual(response.status_code, 200)

    def test_super_admin_delete_book_route(self):
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role", "is_staff"])
        self.client.force_login(self.admin)
        response = self.client.post(reverse("inventory:book_allocation_delete", args=[self.book_allocation.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BookAllocation.objects.filter(pk=self.book_allocation.pk).exists())

    def test_super_admin_delete_tshirt_route(self):
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role", "is_staff"])
        self.client.force_login(self.admin)
        response = self.client.post(reverse("inventory:tshirt_allocation_delete", args=[self.tshirt_allocation.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TshirtAllocation.objects.filter(pk=self.tshirt_allocation.pk).exists())

    def test_super_admin_book_delete_uses_separate_confirmation_page(self):
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role", "is_staff"])
        self.client.force_login(self.admin)
        response = self.client.get(reverse("inventory:book_allocation_delete", args=[self.book_allocation.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete Book Employee Entry")
        self.assertContains(response, "Yes, Delete Book Entry")
        self.assertTrue(BookAllocation.objects.filter(pk=self.book_allocation.pk).exists())

    def test_super_admin_tshirt_delete_uses_separate_confirmation_page(self):
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role", "is_staff"])
        self.client.force_login(self.admin)
        response = self.client.get(reverse("inventory:tshirt_allocation_delete", args=[self.tshirt_allocation.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete T-shirt Employee Entry")
        self.assertContains(response, "Yes, Delete T-shirt Entry")
        self.assertTrue(TshirtAllocation.objects.filter(pk=self.tshirt_allocation.pk).exists())

    def _csrf_client(self):
        return Client(enforce_csrf_checks=True, HTTP_HOST="nexttpinventory.sagarkerhalkar.com")

    def _login_csrf_client(self):
        client = self._csrf_client()
        client.force_login(self.admin)
        return client

    def test_online_https_null_origin_can_delete_book_transaction(self):
        client = self._login_csrf_client()
        url = reverse("inventory:book_allocation_delete", args=[self.book_allocation.pk])
        get_response = client.get(url, secure=True, HTTP_X_FORWARDED_PROTO="https")
        self.assertEqual(get_response.status_code, 200)
        token = get_response.cookies.get("csrftoken")
        if token is not None:
            csrf_token = token.value
        else:
            csrf_token = client.session.get("_csrftoken")
        self.assertTrue(csrf_token)
        response = client.post(
            url,
            {"csrfmiddlewaretoken": csrf_token},
            secure=True,
            HTTP_ORIGIN="null",
            HTTP_X_FORWARDED_PROTO="https",
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BookAllocation.objects.filter(pk=self.book_allocation.pk).exists())

    def test_online_https_null_origin_can_delete_tshirt_transaction(self):
        client = self._login_csrf_client()
        url = reverse("inventory:tshirt_allocation_delete", args=[self.tshirt_allocation.pk])
        get_response = client.get(url, secure=True, HTTP_X_FORWARDED_PROTO="https")
        self.assertEqual(get_response.status_code, 200)
        token = get_response.cookies.get("csrftoken")
        if token is not None:
            csrf_token = token.value
        else:
            csrf_token = client.session.get("_csrftoken")
        self.assertTrue(csrf_token)
        response = client.post(
            url,
            {"csrfmiddlewaretoken": csrf_token},
            secure=True,
            HTTP_ORIGIN="null",
            HTTP_X_FORWARDED_PROTO="https",
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TshirtAllocation.objects.filter(pk=self.tshirt_allocation.pk).exists())

    def test_employee_history_shows_individual_and_bulk_controls_for_super_admin(self):
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role", "is_staff"])
        self.client.force_login(self.admin)
        response = self.client.get(reverse("inventory:employee_history", args=[self.employee_a.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Book Entry")
        self.assertContains(response, "Delete Book Entry")
        self.assertContains(response, "Delete Selected Book Entries")
        self.assertContains(response, "Edit T-shirt Entry")
        self.assertContains(response, "Delete T-shirt Entry")
        self.assertContains(response, "Delete Selected T-shirt Entries")

    def test_super_admin_can_bulk_delete_selected_book_entries_without_deleting_employee(self):
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role", "is_staff"])
        second_book = Book.objects.create(
            asset_id="TRXBOOK2",
            name="Transaction Book 2",
            condition=Book.Condition.GOOD,
            status=Book.Status.ALLOCATED,
            created_by=self.admin,
        )
        second_allocation = BookAllocation.objects.create(
            book=second_book,
            employee_record=self.employee_a,
            allocated_by=self.admin,
            allocated_at=timezone.now(),
            is_active=True,
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("inventory:employee_book_transactions_bulk_delete", args=[self.employee_a.pk]),
            {"book_transaction_ids": [str(self.book_allocation.pk), str(second_allocation.pk)]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BookAllocation.objects.filter(pk__in=[self.book_allocation.pk, second_allocation.pk]).exists())
        self.assertTrue(Employee.objects.filter(pk=self.employee_a.pk).exists())
        self.book.refresh_from_db()
        second_book.refresh_from_db()
        self.assertEqual(self.book.status, Book.Status.IN_LIBRARY)
        self.assertEqual(second_book.status, Book.Status.IN_LIBRARY)

    def test_super_admin_can_bulk_delete_selected_tshirt_entries_and_restore_stock(self):
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role", "is_staff"])
        second_allocation = TshirtAllocation.objects.create(
            employee_record=self.employee_a,
            stock=self.stock_b,
            quantity=3,
            issue_type=TshirtAllocation.IssueType.FREE,
            status=TshirtAllocation.Status.ISSUED,
            requested_by=self.admin,
            requested_at=timezone.now(),
            issued_by=self.admin,
            issued_at=timezone.now(),
        )
        self.stock_b.available_quantity -= 3
        self.stock_b.allocated_quantity += 3
        self.stock_b.save(update_fields=["available_quantity", "allocated_quantity", "updated_at"])

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("inventory:employee_tshirt_transactions_bulk_delete", args=[self.employee_a.pk]),
            {"tshirt_transaction_ids": [str(self.tshirt_allocation.pk), str(second_allocation.pk)]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TshirtAllocation.objects.filter(pk__in=[self.tshirt_allocation.pk, second_allocation.pk]).exists())
        self.assertTrue(Employee.objects.filter(pk=self.employee_a.pk).exists())
        self.stock_a.refresh_from_db()
        self.stock_b.refresh_from_db()
        self.assertEqual(self.stock_a.available_quantity, 10)
        self.assertEqual(self.stock_a.allocated_quantity, 0)
        self.assertEqual(self.stock_b.available_quantity, 20)
        self.assertEqual(self.stock_b.allocated_quantity, 0)

    def test_admin_cannot_delete_book_transaction(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("inventory:book_allocation_delete", args=[self.book_allocation.pk]))
        self.assertRedirects(response, reverse("inventory:dashboard"))
        self.assertTrue(BookAllocation.objects.filter(pk=self.book_allocation.pk).exists())

    def test_admin_cannot_delete_tshirt_transaction(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("inventory:tshirt_allocation_delete", args=[self.tshirt_allocation.pk]))
        self.assertRedirects(response, reverse("inventory:dashboard"))
        self.assertTrue(TshirtAllocation.objects.filter(pk=self.tshirt_allocation.pk).exists())

    def test_staff_cannot_bulk_delete_book_transactions(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("inventory:employee_book_transactions_bulk_delete", args=[self.employee_a.pk]),
            {"book_transaction_ids": [str(self.book_allocation.pk)]},
        )
        self.assertRedirects(response, reverse("inventory:dashboard"))
        self.assertTrue(BookAllocation.objects.filter(pk=self.book_allocation.pk).exists())

    def test_staff_cannot_bulk_delete_tshirt_transactions(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("inventory:employee_tshirt_transactions_bulk_delete", args=[self.employee_a.pk]),
            {"tshirt_transaction_ids": [str(self.tshirt_allocation.pk)]},
        )
        self.assertRedirects(response, reverse("inventory:dashboard"))
        self.assertTrue(TshirtAllocation.objects.filter(pk=self.tshirt_allocation.pk).exists())

