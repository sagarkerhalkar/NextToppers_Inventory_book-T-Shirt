from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.models import Employee, TshirtBrand, User


class PhaseThreeModelTests(TestCase):
    def test_employee_is_non_login_record_and_id_is_immutable(self):
        employee = Employee.objects.create(employee_id="NXTTP0043", full_name="Employee", mobile_number="+919876543210", default_tshirt_size="L")
        self.assertFalse(hasattr(employee, "password"))
        employee.employee_id = "NXTTP0044"
        with self.assertRaises(ValidationError):
            employee.save()

    def test_staff_role_is_displayed_as_data_entry_user(self):
        self.assertEqual(User.Role.STAFF.label, "Data Entry User")

    def test_custom_brand_free_limit(self):
        brand = TshirtBrand.objects.create(name="Mission Jeet", free_quantity_rolling_12_months=3)
        self.assertEqual(brand.free_quantity_rolling_12_months, 3)
