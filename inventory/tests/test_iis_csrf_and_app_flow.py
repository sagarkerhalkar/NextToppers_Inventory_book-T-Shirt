import re

from django.conf import settings
from django.test import Client, TestCase

from inventory.models import User


class IisCsrfAndApplicationFlowTests(TestCase):
    public_host = "156.156.40.51:3458"
    public_origin = "http://156.156.40.51:3458"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            employee_id="NXTTP9001",
            full_name="IIS Flow Test Admin",
            mobile_number="9876509001",
            password="Test1234",
            role=User.Role.SUPER_ADMIN,
            is_active=True,
            must_change_password=False,
        )

    def test_public_iis_origin_accepts_login_csrf_post(self):
        client = Client(enforce_csrf_checks=True)
        login = client.get("/login/?next=/", HTTP_HOST=self.public_host)
        self.assertEqual(login.status_code, 200)
        self.assertIn(settings.CSRF_COOKIE_NAME, login.cookies)

        match = re.search(
            rb'name="csrfmiddlewaretoken" value="([^"]+)"',
            login.content,
        )
        self.assertIsNotNone(match)
        token = match.group(1).decode("ascii")

        response = client.post(
            "/login/?next=/",
            {
                "username": "INVALID_USER",
                "password": "invalid-password",
                "csrfmiddlewaretoken": token,
            },
            HTTP_HOST=self.public_host,
            HTTP_ORIGIN=self.public_origin,
            HTTP_REFERER=f"{self.public_origin}/login/?next=/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login User ID or password is incorrect.")
        self.assertNotContains(response, "CSRF verification failed", status_code=200)

    def test_real_login_reaches_dashboard_and_core_application_pages(self):
        client = Client(enforce_csrf_checks=True)
        login = client.get("/login/?next=/", HTTP_HOST=self.public_host)
        token = re.search(
            rb'name="csrfmiddlewaretoken" value="([^"]+)"',
            login.content,
        ).group(1).decode("ascii")

        response = client.post(
            "/login/?next=/",
            {
                "username": self.user.employee_id,
                "password": "Test1234",
                "csrfmiddlewaretoken": token,
            },
            HTTP_HOST=self.public_host,
            HTTP_ORIGIN=self.public_origin,
            HTTP_REFERER=f"{self.public_origin}/login/?next=/",
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GLOBAL INVENTORY COMMAND CENTER")

        for path in (
            "/",
            "/books/",
            "/employees/",
            "/tshirts/stock/",
            "/reports/",
            "/reports/audit-evidence/",
        ):
            page = client.get(path, HTTP_HOST=self.public_host)
            self.assertEqual(page.status_code, 200, f"Core application page failed: {path}")
            self.assertNotContains(page, "CSRF verification failed", status_code=200)

    def test_public_host_and_origin_are_guaranteed_without_env_file(self):
        self.assertIn("156.156.40.51", settings.ALLOWED_HOSTS)
        self.assertIn(self.public_origin, settings.CSRF_TRUSTED_ORIGINS)
        self.assertEqual(settings.CSRF_COOKIE_NAME, "nexttoppers_csrf_v2")
        self.assertEqual(settings.SESSION_COOKIE_NAME, "nexttoppers_session_v2")
