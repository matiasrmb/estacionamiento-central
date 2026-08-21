import unittest
from unittest.mock import patch

from utils import api_client


class ApiClientSessionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
