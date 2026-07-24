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
        self.assertIn("vendor/bootstrap/bootstrap.min.css", base)
        self.assertIn("vendor/bootstrap/bootstrap.bundle.min.js", base)
        self.assertIn("vendor/chartjs/chart.umd.min.js", dashboard)

    def test_offline_asset_script_removes_source_map_dependencies(self):
        script = (Path(settings.BASE_DIR) / "scripts" / "download_offline_assets.ps1").read_text(encoding="utf-8")
        self.assertIn("sourceMappingURL=", script)
        self.assertIn("[regex]::Replace", script)
        self.assertIn("still contains a source-map reference", script)

    def test_waitress_backend_is_loopback_only(self):
        silent = (Path(settings.BASE_DIR) / "scripts" / "start_server_silent.ps1").read_text(encoding="utf-8")
        visible = (Path(settings.BASE_DIR) / "scripts" / "start_windows.ps1").read_text(encoding="utf-8")
        self.assertIn("127.0.0.1:$BackendPort", silent)
        self.assertIn("127.0.0.1:$BackendPort", visible)
        self.assertNotIn("--listen=0.0.0.0:3458", silent)
        self.assertNotIn("--listen=0.0.0.0:3458", visible)

    def test_iis_script_uses_requested_address_and_microsoft_installers(self):
        script = (Path(settings.BASE_DIR) / "scripts" / "install_iis_reverse_proxy.ps1").read_text(encoding="utf-8")
        self.assertIn('PublicIp = "156.156.40.51"', script)
        self.assertIn("PublicPort = 3458", script)
        self.assertIn("BackendPort = 3460", script)
        self.assertIn("download.microsoft.com", script)
        self.assertIn("Get-AuthenticodeSignature", script)
