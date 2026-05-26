import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from utils import file_cleanup


class FileCleanupTests(unittest.TestCase):
    def test_limpiar_archivos_generados_elimina_solo_archivos_antiguos(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            tickets = base / "tickets"
            tickets.mkdir()

            antiguo = tickets / "ticket_antiguo.pdf"
            reciente = tickets / "ticket_reciente.pdf"
            protegido = tickets / ".gitkeep"
            antiguo.write_text("old", encoding="utf-8")
            reciente.write_text("new", encoding="utf-8")
            protegido.write_text("keep", encoding="utf-8")

            viejo = (datetime.now() - timedelta(days=40)).timestamp()
            os.utime(antiguo, (viejo, viejo))

            resultado = file_cleanup.limpiar_archivos_generados(30, base_path=base)

            self.assertEqual(resultado["eliminados"], 1)
            self.assertFalse(antiguo.exists())
            self.assertTrue(reciente.exists())
            self.assertTrue(protegido.exists())

    @patch.object(file_cleanup, "actualizar_configuracion")
    @patch.object(file_cleanup, "limpiar_archivos_generados")
    @patch.object(file_cleanup, "obtener_configuracion")
    def test_ejecutar_limpieza_periodica_respeta_una_vez_por_dia(
        self,
        obtener_configuracion,
        limpiar_archivos,
        actualizar_configuracion,
    ):
        obtener_configuracion.return_value = {
            "limpieza_automatica_activa": "1",
            "ultima_limpieza_archivos": date.today().isoformat(),
            "dias_conservar_archivos": "30",
        }

        resultado = file_cleanup.ejecutar_limpieza_periodica()

        self.assertFalse(resultado["ejecutada"])
        self.assertEqual(resultado["motivo"], "ya_ejecutada")
        limpiar_archivos.assert_not_called()
        actualizar_configuracion.assert_not_called()

    @patch.object(file_cleanup, "actualizar_configuracion")
    @patch.object(file_cleanup, "limpiar_archivos_generados")
    @patch.object(file_cleanup, "obtener_configuracion")
    def test_ejecutar_limpieza_periodica_actualiza_fecha_si_ejecuta(
        self,
        obtener_configuracion,
        limpiar_archivos,
        actualizar_configuracion,
    ):
        obtener_configuracion.return_value = {
            "limpieza_automatica_activa": "1",
            "ultima_limpieza_archivos": "",
            "dias_conservar_archivos": "30",
        }
        limpiar_archivos.return_value = {"eliminados": 2, "errores": []}

        resultado = file_cleanup.ejecutar_limpieza_periodica()

        self.assertTrue(resultado["ejecutada"])
        self.assertEqual(resultado["eliminados"], 2)
        actualizar_configuracion.assert_called_once_with(
            "ultima_limpieza_archivos",
            date.today().isoformat(),
        )


if __name__ == "__main__":
    unittest.main()
