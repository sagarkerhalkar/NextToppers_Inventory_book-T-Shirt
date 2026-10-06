from django.test import TestCase
from django.urls import reverse

from inventory.models import Book, BookAllocation, Employee, User


class MasterDataCorrectionTests(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            "NXTTP0001", "Super Admin", "+919876543210", "StrongPass123!"
        )
        self.client.force_login(self.super_admin)

    def test_employee_id_can_be_edited_and_mobile_can_be_blank(self):
        employee = Employee.objects.create(
            employee_id="NXTTP0100",
            full_name="Employee One",
            mobile_number=None,
            default_tshirt_size="L",
        )
        response = self.client.post(
            reverse("inventory:employee_edit", args=[employee.pk]),
            {
                "employee_id": "NXTTP0101",
                "full_name": "Employee One",
                "mobile_number": "",
                "email": "",
                "department": "",
                "designation": "",
                "joining_date": "",
                "office_location": "",
                "default_tshirt_size": "L",
                "is_active": "on",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        employee.refresh_from_db()
        self.assertEqual(employee.employee_id, "NXTTP0101")
        self.assertIsNone(employee.mobile_number)

    def test_book_number_publication_and_subject_can_be_edited(self):
        book = Book.objects.create(
            asset_id="OLD-101",
            name="Physics Part 1",
            publication_name="Old Publication",
            subject="Old Subject",
            created_by=self.super_admin,
        )
        response = self.client.post(
            reverse("inventory:book_edit", args=[book.pk]),
            {
                "asset_id": "NEW-101",
                "name": "Physics Part 1",
                "publication_name": "NCERT",
                "subject": "Physics",
                "class_name": "11",
                "stream_name": "Science",
                "isbn": "9780000000000",
                "purchase_date": "",
                "bill_number": "",
                "condition": Book.Condition.GOOD,
            },
        )
        self.assertEqual(response.status_code, 302)
        book.refresh_from_db()
        self.assertEqual(book.asset_id, "NEW-101")
        self.assertEqual(book.publication_name, "NCERT")
        self.assertEqual(book.subject, "Physics")

        search_response = self.client.get(reverse("inventory:book_list"), {"q": "NCERT"})
        self.assertEqual(search_response.context["books"].paginator.count, 1)

    def test_employee_without_history_can_be_deleted(self):
        employee = Employee.objects.create(
            employee_id="NXTTP0200", full_name="Delete Employee", mobile_number=None
        )
        response = self.client.post(reverse("inventory:employee_delete", args=[employee.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Employee.objects.filter(pk=employee.pk).exists())

    def test_employee_with_inventory_history_is_protected_from_deletion(self):
        employee = Employee.objects.create(
            employee_id="NXTTP0201", full_name="History Employee", mobile_number=None
        )
        book = Book.objects.create(name="History Book", created_by=self.super_admin)
        BookAllocation.objects.create(
            book=book, employee_record=employee, allocated_by=self.super_admin
        )
        response = self.client.post(reverse("inventory:employee_delete", args=[employee.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Employee.objects.filter(pk=employee.pk).exists())

    def test_login_user_id_can_be_edited_and_user_can_be_deleted(self):
        login_user = User.objects.create_user(
            "NXTTP0300", "Data User", "+919876543211", "1234", role=User.Role.STAFF
        )
        response = self.client.post(
            reverse("inventory:login_user_edit", args=[login_user.pk]),
            {
                "employee_id": "NXTTP0301",
                "full_name": "Data User",
                "mobile_number": "+919876543211",
                "email": "",
                "role": User.Role.STAFF,
                "department": "",
                "designation": "",
                "office_location": "",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        login_user.refresh_from_db()
        self.assertEqual(login_user.employee_id, "NXTTP0301")

        delete_response = self.client.post(
            reverse("inventory:login_user_delete", args=[login_user.pk])
        )
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=login_user.pk).exists())

    def test_current_login_user_cannot_delete_own_account(self):
        response = self.client.post(
            reverse("inventory:login_user_delete", args=[self.super_admin.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(pk=self.super_admin.pk).exists())
