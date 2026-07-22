from django.core.exceptions import ValidationError
from django.test import TestCase
from inventory.models import Book, User


class UserModelTests(TestCase):
    def test_employee_id_is_immutable(self):
        user = User.objects.create_user("NXTTP0001", "Test User", "+919876543210", "StrongPass123!")
        user.employee_id = "NXTTP0002"
        with self.assertRaises(ValidationError):
            user.save()

    def test_mobile_must_be_unique(self):
        User.objects.create_user("NXTTP0001", "One", "+919876543210", "StrongPass123!")
        with self.assertRaises(ValidationError):
            User.objects.create_user("NXTTP0002", "Two", "+919876543210", "StrongPass123!")


class BookModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("NXTTP0001", "Test User", "+919876543210", "StrongPass123!")

    def test_asset_id_is_generated(self):
        book = Book.objects.create(name="Physics", created_by=self.user)
        self.assertRegex(book.asset_id, r"^BOOK\d{6}$")

    def test_book_with_history_cannot_be_deleted(self):
        book = Book.objects.create(name="Physics", created_by=self.user, condition=Book.Condition.LOST)
        with self.assertRaises(ValidationError):
            book.delete()
