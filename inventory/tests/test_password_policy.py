from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from inventory.forms import AdminPasswordResetForm


class FourCharacterPasswordPolicyTests(SimpleTestCase):
    def test_four_character_password_is_allowed(self):
        validate_password("1234")
        form = AdminPasswordResetForm({
            "new_password": "1234",
            "confirm_password": "1234",
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_three_character_password_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_password("123")
        form = AdminPasswordResetForm({
            "new_password": "123",
            "confirm_password": "123",
        })
        self.assertFalse(form.is_valid())
