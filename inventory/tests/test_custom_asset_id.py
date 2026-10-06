from django.test import TestCase

from inventory.forms import BookForm
from inventory.models import Book, User


class CustomBookAssetIdTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "NXTTP0001", "Admin", "+919876543210", "StrongPass123!", role=User.Role.ADMIN
        )

    def test_custom_asset_id_is_normalised_and_saved(self):
        form = BookForm(data={
            "asset_id": "ntb-0001",
            "name": "Science Book",
            "class_name": "9",
            "stream_name": "",
            "isbn": "",
            "purchase_date": "",
            "bill_number": "",
            "condition": Book.Condition.NEW,
        })
        self.assertTrue(form.is_valid(), form.errors)
        book = form.save(commit=False)
        book.created_by = self.user
        book.save()
        self.assertEqual(book.asset_id, "NTB-0001")

    def test_blank_asset_id_uses_automatic_number(self):
        form = BookForm(data={
            "asset_id": "",
            "name": "Mathematics Book",
            "class_name": "10",
            "stream_name": "",
            "isbn": "",
            "purchase_date": "",
            "bill_number": "",
            "condition": Book.Condition.GOOD,
        })
        self.assertTrue(form.is_valid(), form.errors)
        book = form.save(commit=False)
        book.created_by = self.user
        book.save()
        self.assertRegex(book.asset_id, r"^BOOK\d{6}$")

    def test_invalid_asset_id_is_rejected(self):
        form = BookForm(data={
            "asset_id": "bad id!",
            "name": "English Book",
            "class_name": "8",
            "stream_name": "",
            "isbn": "",
            "purchase_date": "",
            "bill_number": "",
            "condition": Book.Condition.GOOD,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("asset_id", form.errors)
