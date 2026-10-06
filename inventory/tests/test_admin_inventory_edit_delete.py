from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from inventory.models import Book, TshirtBrand, TshirtPurchase, TshirtStock, User


class AdminInventoryEditDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            employee_id="NXTTP9701",
            full_name="Admin Test",
            mobile_number="+919876509701",
            password="Test1234",
            role=User.Role.ADMIN,
            is_active=True,
            must_change_password=False,
        )
        cls.staff = User.objects.create_user(
            employee_id="NXTTP9702",
            full_name="Staff Test",
            mobile_number="+919876509702",
            password="Test1234",
            role=User.Role.STAFF,
            is_active=True,
            must_change_password=False,
        )
        cls.book = Book.objects.create(
            asset_id="ADMBOOK1",
            name="Admin Editable Book",
            created_by=cls.admin,
        )
        cls.brand = TshirtBrand.objects.create(name="Admin Test Brand", is_active=True)
        cls.stock = TshirtStock.objects.create(
            brand=cls.brand,
            size=User.TshirtSize.L,
            available_quantity=10,
            allocated_quantity=0,
        )
        cls.purchase = TshirtPurchase.objects.create(
            stock=cls.stock,
            purchase_date="2026-10-01",
            vendor="Vendor A",
            bill_number="B-1",
            quantity=10,
            total_cost=Decimal("1000.00"),
            created_by=cls.admin,
        )

    def test_admin_can_edit_book(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("inventory:book_edit", args=[self.book.pk]),
            {
                "asset_id": "ADMBOOK1",
                "name": "Updated Book Name",
                "publication_name": "",
                "subject": "",
                "class_name": "",
                "stream_name": "",
                "isbn": "",
                "purchase_date": "",
                "bill_number": "",
                "condition": Book.Condition.GOOD,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.book.refresh_from_db()
        self.assertEqual(self.book.name, "Updated Book Name")

    def test_staff_cannot_edit_book(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("inventory:book_edit", args=[self.book.pk]))
        self.assertRedirects(response, reverse("inventory:dashboard"))

    def test_admin_can_delete_book_without_history(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("inventory:book_delete", args=[self.book.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())

    def test_admin_can_edit_tshirt_purchase_and_stock_is_reconciled(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("inventory:tshirt_purchase_edit", args=[self.purchase.pk]),
            {
                "stock": str(self.stock.pk),
                "purchase_date": "2026-10-01",
                "vendor": "Vendor B",
                "bill_number": "B-2",
                "quantity": "7",
                "total_cost": "900.00",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.purchase.refresh_from_db()
        self.stock.refresh_from_db()
        self.assertEqual(self.purchase.quantity, 7)
        self.assertEqual(self.purchase.vendor, "Vendor B")
        self.assertEqual(self.stock.available_quantity, 7)

    def test_admin_can_delete_tshirt_purchase_and_stock_is_reconciled(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("inventory:tshirt_purchase_delete", args=[self.purchase.pk]))
        self.assertEqual(response.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.available_quantity, 0)
        self.assertFalse(TshirtPurchase.objects.filter(pk=self.purchase.pk).exists())

    def test_staff_cannot_open_tshirt_purchase_history(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("inventory:tshirt_purchase_list"))
        self.assertRedirects(response, reverse("inventory:dashboard"))
