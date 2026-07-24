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
            mobile_number="+919876509001",
            password="Test1234",
            role=User.Role.SUPER_ADMIN,
            is_active=True,
            must_change_password=False,
        )

    def _login_nonce(self, client):
        response = client.get("/login/?next=/", HTTP_HOST=self.public_host)
        self.assertEqual(response.status_code, 200)
        match = re.search(rb'name="login_nonce" value="([^"]+)"', response.content)
        self.assertIsNotNone(match)
        self.assertIn(settings.SESSION_COOKIE_NAME, response.cookies)
        self.assertNotContains(response, 'name="csrfmiddlewaretoken"', status_code=200)
        return match.group(1).decode("ascii")

    def test_invalid_login_post_uses_one_time_session_nonce_not_csrf_cookie(self):
        client = Client(enforce_csrf_checks=True)
        nonce = self._login_nonce(client)
        response = client.post(
            "/login/",
            {
                "username": "INVALID_USER",
                "password": "invalid-password",
                "login_nonce": nonce,
            },
            HTTP_HOST=self.public_host,
            HTTP_ORIGIN=self.public_origin,
            HTTP_REFERER=f"{self.public_origin}/login/",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct employee id and password")
        self.assertNotContains(response, "CSRF verification failed", status_code=200)
        self.assertRegex(response.content.decode(), r'name="login_nonce" value="[^"]+"')

    def test_successful_login_reaches_dashboard_and_core_application_pages(self):
        client = Client(enforce_csrf_checks=True)
        nonce = self._login_nonce(client)
        response = client.post(
            "/login/",
            {
                "username": self.user.employee_id,
                "password": "Test1234",
                "login_nonce": nonce,
            },
            HTTP_HOST=self.public_host,
            HTTP_ORIGIN=self.public_origin,
            HTTP_REFERER=f"{self.public_origin}/login/",
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Next Toppers Inventory System")
        self.assertContains(response, 'data-inventory-tab="books"')
        self.assertContains(response, 'data-inventory-tab="tshirts"')

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

        token_response = client.get(
            "/health/session-csrf-token/",
            HTTP_HOST=self.public_host,
        )
        self.assertEqual(token_response.status_code, 200)
        token = token_response.json()["csrfToken"]
        probe = client.post(
            "/health/session-csrf-probe/",
            HTTP_HOST=self.public_host,
            HTTP_ORIGIN=self.public_origin,
            HTTP_REFERER=f"{self.public_origin}/",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(probe.status_code, 200)
        self.assertEqual(probe.content, b"SESSION_CSRF_OK")

    def test_session_csrf_probe_rejects_missing_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(
            "/health/session-csrf-probe/",
            HTTP_HOST=self.public_host,
            HTTP_ORIGIN=self.public_origin,
            HTTP_REFERER=f"{self.public_origin}/",
        )
        self.assertEqual(response.status_code, 403)

    def test_public_host_and_session_security_are_guaranteed(self):
        self.assertIn("156.156.40.51", settings.ALLOWED_HOSTS)
        self.assertIn(self.public_origin, settings.CSRF_TRUSTED_ORIGINS)
        self.assertTrue(settings.CSRF_USE_SESSIONS)
        self.assertEqual(settings.CSRF_COOKIE_NAME, "nexttoppers_csrf_v3")
        self.assertEqual(settings.SESSION_COOKIE_NAME, "nexttoppers_session_v3")
