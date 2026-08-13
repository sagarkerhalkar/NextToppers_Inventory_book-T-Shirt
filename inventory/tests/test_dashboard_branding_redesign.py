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

    def test_uploaded_brand_logo_is_rendered_and_served_in_production(self):
        branding = BrandingSettings.load()
        branding.organization_name = "Next Toppers Inventory System"
        branding.app_logo = self._png()
        branding.save()

        dashboard = self.client.get("/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "nt-logo-module")
        self.assertContains(dashboard, branding.app_logo.url)

        logo = self.client.get(branding.app_logo.url)
        self.assertEqual(logo.status_code, 200)
        self.assertEqual(logo["Content-Type"], "image/png")

        private_media = self.client.get("/media/payment_proofs/private.pdf")
        self.assertEqual(private_media.status_code, 404)

    def test_branding_save_uses_one_time_nonce_without_csrf_cookie_dependency(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        page = client.get("/settings/branding/")
        self.assertEqual(page.status_code, 200)
        html = page.content.decode("utf-8")
        form_match = re.search(r'<form[^>]+id="brandingForm".*?</form>', html, re.S)
        self.assertIsNotNone(form_match)
        branding_form_html = form_match.group(0)
        nonce_match = re.search(r'name="branding_nonce" value="([^"]+)"', branding_form_html)
        self.assertIsNotNone(nonce_match)
        self.assertNotIn('name="csrfmiddlewaretoken"', branding_form_html)

        response = client.post(
            "/settings/branding/",
            {
                "branding_nonce": nonce_match.group(1),
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
        self.assertEqual(client.get(branding.app_logo.url).status_code, 200)

    def test_logout_does_not_require_csrf_cookie(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        response = client.get("/logout/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")
        dashboard = client.get("/")
        self.assertEqual(dashboard.status_code, 302)
        self.assertIn("/login/", dashboard.url)
