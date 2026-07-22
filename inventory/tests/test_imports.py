from io import BytesIO

from django.test import TestCase
from openpyxl import Workbook

from inventory.import_services import import_books, import_employees, import_tshirt_stock
from inventory.models import Book, Employee, TshirtBrand, TshirtPurchase, TshirtStock, User


def workbook_file(headers, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    output.name = "import.xlsx"
    return output


class BulkImportTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("NXTTP0001", "Admin User", "+919876543210", "StrongPass123!", role=User.Role.ADMIN)

    def test_employee_import_creates_non_login_employee_and_reports_duplicate(self):
        file = workbook_file(["employee_id", "full_name", "mobile_number", "default_tshirt_size"], [["NXTTP0043", "Employee One", "+919876543211", "L"], ["NXTTP0043", "Duplicate", "+919876543212", "M"]])
        result = import_employees(file, self.admin)
        self.assertEqual(result.created, 1)
        self.assertEqual(result.failed, 1)
        self.assertTrue(Employee.objects.filter(employee_id="NXTTP0043").exists())
        self.assertFalse(User.objects.filter(employee_id="NXTTP0043").exists())

    def test_book_import_generates_asset_id(self):
        file = workbook_file(["book_name", "class_name", "condition"], [["Physics", "11", "GOOD"]])
        result = import_books(file, self.admin)
        self.assertEqual(result.created, 1)
        self.assertRegex(Book.objects.get(name="Physics").asset_id, r"^BOOK\d{6}$")

    def test_tshirt_import_updates_stock_and_purchase_history(self):
        file = workbook_file(["brand", "size", "quantity", "free_allowance", "low_stock_threshold"], [["Next Toppers", "L", 25, 5, 4]])
        result = import_tshirt_stock(file, self.admin)
        self.assertEqual(result.successful, 1)
        brand = TshirtBrand.objects.get(name="Next Toppers")
        stock = TshirtStock.objects.get(brand=brand, size="L")
        self.assertEqual(stock.available_quantity, 25)
        self.assertEqual(stock.low_stock_threshold, 4)
        self.assertEqual(TshirtPurchase.objects.filter(stock=stock).count(), 1)
