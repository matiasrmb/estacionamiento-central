from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from utils import api_client


class ApiClientSessionTests(unittest.TestCase):
    def test_api_base_url_defaults_to_localhost_without_api_section(self):
        with TemporaryDirectory() as config_dir:
            Path(config_dir, "config.ini").write_text("[mysql]\nhost=localhost\n", encoding="utf-8")

            with patch.object(api_client, "get_base_paths", return_value=[config_dir]):
                self.assertEqual(api_client._api_base_url(), "http://localhost:8000/api/v1")

    def test_api_base_url_uses_configured_value(self):
        with TemporaryDirectory() as config_dir:
            Path(config_dir, "config.ini").write_text(
                "[api]\nbase_url=http://api.example.test:8100/api/v1\n", encoding="utf-8"
            )

            with patch.object(api_client, "get_base_paths", return_value=[config_dir]):
                self.assertEqual(api_client._api_base_url(), "http://api.example.test:8100/api/v1")

    def test_api_base_url_trims_configured_trailing_slash(self):
        with TemporaryDirectory() as config_dir:
            Path(config_dir, "config.ini").write_text(
                "[api]\nbase_url=http://api.example.test:8100/api/v1/\n", encoding="utf-8"
            )

            with patch.object(api_client, "get_base_paths", return_value=[config_dir]):
                self.assertEqual(api_client._api_base_url(), "http://api.example.test:8100/api/v1")

    @patch.object(api_client, "_request", return_value={"access_token": "token"})
    @patch.object(api_client, "desktop_device_id", return_value="desktop-test")
    def test_desktop_login_sends_its_device_identity(self, device_id, request):
        api_client.autenticar("admin", "secreta")

        request.assert_called_once_with(
            "POST",
            "/auth/login",
            {"usuario": "admin", "clave": "secreta", "device_id": "desktop-test"},
        )

    @patch.object(api_client, "_request", return_value={"ok": True})
    def test_desktop_logout_uses_only_its_bearer_token(self, request):
        api_client.cerrar_sesion("desktop-token")

        request.assert_called_once_with("POST", "/auth/logout", token="desktop-token")

    @patch.object(api_client, "_request", return_value={"resumen": {}})
    def test_desktop_session_summary_uses_its_bearer_token(self, request):
        api_client.obtener_resumen_sesion("desktop-token")

        request.assert_called_once_with("GET", "/auth/session-summary", token="desktop-token")

    @patch.object(api_client, "_request", return_value={
        "version": "2026-09-29",
        "metrics": [
            {"name": "collected_sources_total", "label": "All collected sources"},
            {"name": "operational_expense_total", "label": "Operational expenses"},
            {"name": "net_revenue_total", "label": "Net revenue"},
        ],
    })
    def test_reporting_metric_catalog_uses_canonical_endpoint(self, request):
        result = api_client.obtener_catalogo_metricas_reporting("desktop-token")

        self.assertEqual(
            [metric["name"] for metric in result["metrics"]],
            ["collected_sources_total", "operational_expense_total", "net_revenue_total"],
        )
        request.assert_called_once_with("GET", "/reporting/metric-catalog", token="desktop-token")

    @patch.object(api_client, "_request", return_value={"metrics": {}})
    def test_reporting_dashboard_uses_canonical_endpoint_without_query_params(self, request):
        result = api_client.obtener_dashboard_reporting("desktop-token")

        self.assertEqual(result, {"metrics": {}})
        request.assert_called_once_with("GET", "/reporting/dashboard", token="desktop-token")

    @patch.object(api_client, "_request", return_value={"report_id": "closed-42"})
    def test_closed_report_uses_canonical_endpoint(self, request):
        result = api_client.obtener_reporte_cerrado("desktop-token", "closure-42")

        self.assertEqual(result, {"report_id": "closed-42"})
        request.assert_called_once_with(
            "GET",
            "/reporting/reports/closed/closure-42",
            token="desktop-token",
        )

    @patch.object(api_client, "_request", return_value={"format": "pdf"})
    def test_closed_report_pdf_export_uses_canonical_endpoint(self, request):
        result = api_client.exportar_reporte_cerrado("desktop-token", "closure-42", "pdf")

        self.assertEqual(result, {"format": "pdf"})
        request.assert_called_once_with(
            "GET",
            "/reporting/exports/closure-42.pdf",
            token="desktop-token",
        )

    @patch.object(api_client, "_request", return_value={"format": "xlsx"})
    def test_closed_report_xlsx_export_uses_canonical_endpoint(self, request):
        result = api_client.exportar_reporte_cerrado("desktop-token", "closure-42", "xlsx")

        self.assertEqual(result, {"format": "xlsx"})
        request.assert_called_once_with(
            "GET",
            "/reporting/exports/closure-42.xlsx",
            token="desktop-token",
        )

    def test_closed_report_export_rejects_non_pdf_xlsx_format(self):
        with self.assertRaises(ValueError) as context:
            api_client.exportar_reporte_cerrado("desktop-token", "closure-42", "csv")

        self.assertEqual(str(context.exception), "Formato de exportación inválido.")


if __name__ == "__main__":
    unittest.main()
