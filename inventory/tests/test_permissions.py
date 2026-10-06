from django.test import TestCase
from inventory.models import User
from inventory.permissions import can_manage_target


class PermissionTests(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser("NXTTP0001", "Super", "+919876543210", "StrongPass123!")
        self.admin = User.objects.create_user("NXTTP0002", "Admin", "+919876543211", "StrongPass123!", role=User.Role.ADMIN)
        self.staff = User.objects.create_user("NXTTP0003", "Staff", "+919876543212", "StrongPass123!")

    def test_admin_cannot_manage_super_admin(self):
        self.assertFalse(can_manage_target(self.admin, self.super_admin))

    def test_admin_can_manage_staff(self):
        self.assertTrue(can_manage_target(self.admin, self.staff))


class PasswordResetFlowTests(TestCase):
    def test_reset_flag_requires_change(self):
        user = User.objects.create_user("NXTTP0004", "Reset User", "+919876543213", "StrongPass123!")
        user.must_change_password = True
        user.save(update_fields=["must_change_password"])
        self.client.force_login(user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("change-temporary-password", response.url)
