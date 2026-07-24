import re
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from PIL import Image

from inventory.models import BrandingSettings, User


class DashboardBrandingRedesignTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            employee_id="NXTTP9901",
            full_name="Dashboard Test Admin",
            mobile_number="+919876509901",
            password="Test1234",
            role=User.Role.SUPER_ADMIN,
            is_active=True,
            must_change_password=False,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    @staticmethod
    def _png(name="logo.png"):
        output = BytesIO()
        Image.new("RGBA", (120, 120), (15, 118, 110, 255)).save(output, format="PNG")
        return SimpleUploadedFile(name, output.getvalue(), content_type="image/png")

    def test_dashboard_has_two_overview_tabs_and_new_title(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Next Toppers Inventory System")
        self.assertContains(response, 'data-inventory-tab="books"')
        self.assertContains(response, 'data-inventory-tab="tshirts"')
        self.assertContains(response, 'data-inventory-panel="books"')
        self.assertContains(response, 'data-inventory-panel="tshirts"')
        self.assertNotContains(response, "Control every Book and T-shirt movement")

    def test_uploaded_brand_logo_is_rendered_in_3d_dashboard_module(self):
        branding = BrandingSettings.load()
        branding.organization_name = "Next Toppers Inventory System"
        branding.app_logo = self._png()
        branding.save()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nt-logo-module")
        self.assertContains(response, branding.app_logo.url)

    def test_branding_save_uses_one_time_nonce_without_csrf_cookie_dependency(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        page = client.get("/settings/branding/")
        self.assertEqual(page.status_code, 200)
        match = re.search(rb'name="branding_nonce" value="([^"]+)"', page.content)
        self.assertIsNotNone(match)
        self.assertNotContains(page, 'name="csrfmiddlewaretoken"', status_code=200)

        response = client.post(
            "/settings/branding/",
            {
                "branding_nonce": match.group(1).decode("ascii"),
                "organization_name": "Next Toppers Inventory System",
                "app_logo": self._png("new-logo.png"),
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Branding and logo updated successfully.")
        branding = BrandingSettings.load()
        self.assertEqual(branding.organization_name, "Next Toppers Inventory System")
        self.assertTrue(bool(branding.app_logo))
