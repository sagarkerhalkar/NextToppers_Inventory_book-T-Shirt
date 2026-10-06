from django.test import TestCase

from inventory.models import Employee, TshirtBrand, User


class PhaseThreeModelTests(TestCase):
    def test_employee_is_non_login_record_and_id_can_be_corrected(self):
        employee = Employee.objects.create(employee_id="NXTTP0043", full_name="Employee", mobile_number="+919876543210", default_tshirt_size="L")
        self.assertFalse(hasattr(employee, "password"))
        employee.employee_id = "NXTTP0044"
        employee.save()
        employee.refresh_from_db()
        self.assertEqual(employee.employee_id, "NXTTP0044")

    def test_employee_mobile_number_is_optional(self):
        first = Employee.objects.create(employee_id="NXTTP0045", full_name="Employee One", mobile_number=None)
        second = Employee.objects.create(employee_id="NXTTP0046", full_name="Employee Two", mobile_number="")
        self.assertIsNone(first.mobile_number)
        second.refresh_from_db()
        self.assertIsNone(second.mobile_number)

    def test_staff_role_is_displayed_as_data_entry_user(self):
        self.assertEqual(User.Role.STAFF.label, "Data Entry User")

    def test_custom_brand_free_limit(self):
        brand = TshirtBrand.objects.create(name="Mission Jeet", free_quantity_rolling_12_months=3)
        self.assertEqual(brand.free_quantity_rolling_12_months, 3)
