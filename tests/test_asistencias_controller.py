import unittest
from contextlib import contextmanager
from datetime import date, datetime, time
from unittest.mock import patch

from controllers import asistencias_controller


class FakeCursor:
    def __init__(self, fetchall_results=None):
        self.fetchall_results = list(fetchall_results or [])
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class ObtenerAsistenciasTests(unittest.TestCase):
    @patch.object(asistencias_controller, "db_cursor")
    def test_obtiene_asistencias_sin_filtros(self, db_cursor):
        filas = [{"usuario": "admin", "total_recaudado": 1000}]
        cursor = FakeCursor(fetchall_results=[filas])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = asistencias_controller.obtener_asistencias()

        self.assertEqual(resultado, filas)
        db_cursor.assert_called_once_with(dictionary=True)
        query, params = cursor.executed[0]
        self.assertIn("FROM asistencias", query)
        self.assertIn("ORDER BY hora_inicio DESC", query)
        self.assertEqual(params, [])

    @patch.object(asistencias_controller, "db_cursor")
    def test_filtra_por_usuario_y_rango_de_fechas(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[]])
        db_cursor.return_value = fake_db_cursor(cursor)

        asistencias_controller.obtener_asistencias(
            usuario="admin",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 1, 31),
        )

        query, params = cursor.executed[0]
        self.assertIn("AND usuario = %s", query)
        self.assertIn("AND hora_inicio BETWEEN %s AND %s", query)
        self.assertEqual(params[0], "admin")
        self.assertEqual(params[1], datetime.combine(date(2026, 1, 1), time.min))
        self.assertEqual(params[2], datetime.combine(date(2026, 1, 31), time.max))


if __name__ == "__main__":
    unittest.main()
