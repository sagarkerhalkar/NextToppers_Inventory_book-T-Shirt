from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse


class IisOfflineDeploymentTests(SimpleTestCase):
    def test_all_user_templates_do_not_call_external_cdn_assets(self):
        template_paths = [
            Path(settings.BASE_DIR) / "templates" / "inventory" / "base.html",
            Path(settings.BASE_DIR) / "templates" / "inventory" / "dashboard.html",
            Path(settings.BASE_DIR) / "templates" / "registration" / "login.html",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in template_paths)
        self.assertNotIn("fonts.googleapis.com", combined)
        self.assertNotIn("fonts.gstatic.com", combined)
        self.assertNotIn("cdn.jsdelivr.net", combined)
        self.assertNotIn("chart.umd.min.js", combined)
        self.assertNotIn("new Chart(", combined)
        self.assertIn("vendor/bootstrap/bootstrap.min.css", combined)

        base = template_paths[0].read_text(encoding="utf-8")
        dashboard = template_paths[1].read_text(encoding="utf-8")
        login = template_paths[2].read_text(encoding="utf-8")
        self.assertIn("vendor/bootstrap/bootstrap.bundle.min.js", base)
        self.assertIn("vendor/bootstrap/bootstrap.min.css", login)
        self.assertIn("local-bar-chart", dashboard)
        self.assertIn("local-donut", dashboard)

    def test_static_and_media_urls_are_absolute_for_nested_iis_routes(self):
        self.assertEqual(settings.STATIC_URL, "/static/")
        self.assertEqual(settings.MEDIA_URL, "/media/")

    def test_health_endpoint_is_plain_and_does_not_require_login(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"NEXT_TOPPERS_INVENTORY_OK")
        self.assertEqual(response["Content-Type"], "text/plain")

    def test_waitress_backend_is_loopback_only_and_starts_executable_directly(self):
        silent = (Path(settings.BASE_DIR) / "scripts" / "start_server_silent.ps1").read_text(encoding="utf-8")
        visible = (Path(settings.BASE_DIR) / "scripts" / "start_windows.ps1").read_text(encoding="utf-8")
        self.assertIn("127.0.0.1:$BackendPort", silent)
        self.assertIn("127.0.0.1:$BackendPort", visible)
        self.assertNotIn("--listen=0.0.0.0:3458", silent)
        self.assertNotIn("--listen=0.0.0.0:3458", visible)
        self.assertIn("waitress-serve.exe", silent)
        self.assertIn("-FilePath $WaitressExe", silent)
        self.assertIn('"--listen=127.0.0.1:$BackendPort"', silent)
        self.assertNotIn('-ArgumentList "`"$Runner`""', silent)
        self.assertNotIn("manage.py check 2>&1", silent)
        self.assertNotIn("backend_preflight.log", silent)
        self.assertIn("harmless dependency warnings", silent)
        self.assertIn("backend_stderr.log", silent)
        self.assertIn("Start-Process", silent)

    def test_iis_script_uses_requested_address_and_microsoft_installers(self):
        script = (Path(settings.BASE_DIR) / "scripts" / "install_iis_reverse_proxy.ps1").read_text(encoding="utf-8")
        self.assertIn('PublicIp = "156.156.40.51"', script)
        self.assertIn("PublicPort = 3458", script)
        self.assertIn("BackendPort = 3460", script)
        self.assertIn("download.microsoft.com", script)
        self.assertIn("Get-AuthenticodeSignature", script)

    def test_offline_asset_script_does_not_download_chart_library(self):
        script = (Path(settings.BASE_DIR) / "scripts" / "download_offline_assets.ps1").read_text(encoding="utf-8")
        self.assertNotIn("chart.js@", script.lower())
        self.assertNotIn("chart.umd.min.js", script.lower())
        self.assertIn("No Chart.js download is required", script)
