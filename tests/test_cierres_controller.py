import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from controllers import cierres_controller


class FakeCursor:
    def __init__(self, fetchall_results=None, fetchone_results=None):
        self.fetchall_results = list(fetchall_results or [])
        self.fetchone_results = list(fetchone_results or [])
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def close(self):
        self.closed = True


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class RealizarCierreDiarioTests(unittest.TestCase):
    @patch.object(cierres_controller, "generar_pdf_cierre")
    @patch.object(cierres_controller, "db_cursor")
    def test_retorna_false_si_no_hay_registros_para_cerrar(self, db_cursor, generar_pdf):
        cursor = FakeCursor(fetchall_results=[[]])
        db_cursor.return_value = fake_db_cursor(cursor)

        exito, mensaje = cierres_controller.realizar_cierre_diario("admin")

        self.assertFalse(exito)
        self.assertEqual(mensaje, "No hay registros para cerrar hoy.")
        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        generar_pdf.assert_not_called()

    @patch.object(cierres_controller, "generar_pdf_cierre")
    @patch.object(cierres_controller, "db_cursor")
    def test_cierra_registros_inserta_resumen_marca_ingresos_y_genera_pdf(
        self,
        db_cursor,
        generar_pdf,
    ):
        registros = [
            {
                "id_ingreso": 1,
                "fecha_hora_ingreso": datetime(2026, 1, 1, 9, 0),
                "fecha_hora_salida": datetime(2026, 1, 1, 10, 0),
                "tarifa_aplicada": 1000,
            },
            {
                "id_ingreso": 2,
                "fecha_hora_ingreso": datetime(2026, 1, 1, 9, 30),
                "fecha_hora_salida": datetime(2026, 1, 1, 11, 0),
                "tarifa_aplicada": 1500,
            },
        ]
        cursor = FakeCursor(
            fetchall_results=[registros],
            fetchone_results=[{"cantidad": 2, "total": 600}],
        )
        db_cursor.return_value = fake_db_cursor(cursor)

        exito, mensaje = cierres_controller.realizar_cierre_diario("admin")

        self.assertTrue(exito)
        self.assertIn("$3100", mensaje)
        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        generar_pdf.assert_called_once()
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO cierres_diarios", consultas)
        self.assertIn("UPDATE ingresos SET cerrado = TRUE", consultas)


if __name__ == "__main__":
    unittest.main()
