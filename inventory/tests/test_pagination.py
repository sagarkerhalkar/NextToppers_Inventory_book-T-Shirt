from django.test import TestCase
from django.urls import reverse

from inventory.models import Book, BookAllocation, Employee, TshirtAllocation, TshirtBrand, TshirtStock, User


class ScalableListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "NXTTP0001", "Admin", "+919876543210", "StrongPass123!", role=User.Role.ADMIN
        )
        self.client.force_login(self.user)

    def test_books_default_to_twenty_and_allow_thirty(self):
        for number in range(45):
            Book.objects.create(name=f"Book {number:03d}", created_by=self.user)

        response = self.client.get(reverse("inventory:book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["books"]), 20)
        self.assertEqual(response.context["books"].paginator.count, 45)

        response = self.client.get(reverse("inventory:book_list"), {"page_size": "30"})
        self.assertEqual(len(response.context["books"]), 30)

        response = self.client.get(reverse("inventory:book_list"), {"page": "2"})
        self.assertEqual(len(response.context["books"]), 20)

    def test_book_search_by_name_and_asset_id(self):
        target = Book.objects.create(asset_id="SCI9-001", name="Special Science", created_by=self.user)
        Book.objects.create(name="Other Book", created_by=self.user)

        by_name = self.client.get(reverse("inventory:book_list"), {"q": "Special Science"})
        self.assertEqual(by_name.context["books"].paginator.count, 1)
        self.assertEqual(by_name.context["books"][0].pk, target.pk)

        by_id = self.client.get(reverse("inventory:book_list"), {"q": "SCI9-001"})
        self.assertEqual(by_id.context["books"].paginator.count, 1)

    def test_employee_and_tshirt_lists_are_paginated(self):
        for number in range(35):
            Employee.objects.create(
                employee_id=f"NXTTP{number + 100:04d}",
                full_name=f"Employee {number:03d}",
                mobile_number=f"+91987{number + 6000000:07d}",
            )
        employee_response = self.client.get(reverse("inventory:employee_list"))
        self.assertEqual(len(employee_response.context["employees"]), 20)

        for number in range(35):
            brand = TshirtBrand.objects.create(name=f"Brand {number:03d}")
            TshirtStock.objects.create(brand=brand, size="L")
        stock_response = self.client.get(reverse("inventory:tshirt_stock_list"), {"page_size": "30"})
        self.assertEqual(len(stock_response.context["stocks"]), 30)

    def test_employee_360_paginates_book_and_tshirt_history_separately(self):
        employee = Employee.objects.create(
            employee_id="NXTTP0099", full_name="History Employee", mobile_number="+919876543299"
        )
        brand = TshirtBrand.objects.create(name="Next Toppers", free_quantity_rolling_12_months=50)
        stock = TshirtStock.objects.create(brand=brand, size="L", available_quantity=50)
        for number in range(25):
            book = Book.objects.create(name=f"History Book {number:03d}", created_by=self.user)
            BookAllocation.objects.create(book=book, employee_record=employee, allocated_by=self.user)
            TshirtAllocation.objects.create(
                employee_record=employee,
                stock=stock,
                quantity=1,
                issue_type=TshirtAllocation.IssueType.FREE,
                status=TshirtAllocation.Status.ISSUED,
                requested_by=self.user,
                issued_by=self.user,
            )

        response = self.client.get(reverse("inventory:employee_history", args=[employee.pk]))
        self.assertEqual(len(response.context["book_history"]), 20)
        self.assertEqual(len(response.context["tshirt_history"]), 20)
        self.assertEqual(response.context["book_history"].paginator.count, 25)
        self.assertEqual(response.context["tshirt_history"].paginator.count, 25)
