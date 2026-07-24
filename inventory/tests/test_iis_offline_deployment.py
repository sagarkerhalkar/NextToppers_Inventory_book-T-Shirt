from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class IisOfflineDeploymentTests(SimpleTestCase):
    def test_templates_do_not_call_external_cdn_assets(self):
        base = (Path(settings.BASE_DIR) / "templates" / "inventory" / "base.html").read_text(encoding="utf-8")
        dashboard = (Path(settings.BASE_DIR) / "templates" / "inventory" / "dashboard.html").read_text(encoding="utf-8")
        combined = base + dashboard
        self.assertNotIn("fonts.googleapis.com", combined)
        self.assertNotIn("fonts.gstatic.com", combined)
        self.assertNotIn("cdn.jsdelivr.net", combined)
        self.assertNotIn("chart.umd.min.js", dashboard)
        self.assertNotIn("new Chart(", dashboard)
        self.assertIn("vendor/bootstrap/bootstrap.min.css", base)
        self.assertIn("vendor/bootstrap/bootstrap.bundle.min.js", base)
        self.assertIn("local-bar-chart", dashboard)
        self.assertIn("local-donut", dashboard)

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
