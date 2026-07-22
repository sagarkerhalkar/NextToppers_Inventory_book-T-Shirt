from django.test import TestCase
from inventory.models import Book, TshirtBrand, TshirtStock, User
from inventory.services import allocate_book, free_entitlement, issue_free_tshirts, return_book


class InventoryServiceTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("NXTTP0001", "Admin", "+919876543210", "StrongPass123!", role=User.Role.ADMIN)
        self.employee = User.objects.create_user("NXTTP0002", "Employee", "+919876543211", "StrongPass123!")

    def test_book_allocate_and_return(self):
        book = Book.objects.create(name="Mathematics", created_by=self.admin)
        allocation = allocate_book(book=book, employee=self.employee, actor=self.admin)
        book.refresh_from_db()
        self.assertEqual(book.status, Book.Status.ALLOCATED)
        return_book(allocation=allocation, condition=Book.Condition.GOOD, note="Returned in good condition", actor=self.admin)
        book.refresh_from_db()
        self.assertEqual(book.status, Book.Status.IN_LIBRARY)

    def test_rolling_entitlement_blocks_extra_free_issue(self):
        brand = TshirtBrand.objects.create(name="Next Toppers", free_quantity_rolling_12_months=1)
        stock = TshirtStock.objects.create(brand=brand, size="L", available_quantity=5)
        issue_free_tshirts(employee=self.employee, stock=stock, quantity=1, actor=self.admin)
        self.assertEqual(free_entitlement(self.employee, brand)["remaining"], 0)
        with self.assertRaises(ValueError):
            issue_free_tshirts(employee=self.employee, stock=stock, quantity=1, actor=self.admin)
