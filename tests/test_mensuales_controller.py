import unittest
from contextlib import contextmanager
from unittest.mock import patch

from controllers import mensuales_controller


class FakeCursor:
    def __init__(self, fetchone_results=None, fetchall_results=None):
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class MensualesControllerTests(unittest.TestCase):
    @patch.object(mensuales_controller, "db_cursor")
    def test_obtener_mensuales_retorna_clientes_activos(self, db_cursor):
        mensuales = [{"id_vehiculo": 1, "patente": "ABC123", "tarifa_mensual": 50000}]
        cursor = FakeCursor(fetchall_results=[mensuales])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = mensuales_controller.obtener_mensuales()

        self.assertEqual(resultado, mensuales)
        db_cursor.assert_called_once_with(dictionary=True)

    @patch.object(mensuales_controller, "db_cursor")
    def test_agregar_mensual_actualiza_si_patente_existe(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[(1,)])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = mensuales_controller.agregar_mensual("ABC123")

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("SELECT * FROM vehiculos", consultas)
        self.assertIn("UPDATE vehiculos SET tipo_cliente = 'mensual'", consultas)
        self.assertNotIn("INSERT INTO vehiculos", consultas)

    @patch.object(mensuales_controller, "db_cursor")
    def test_agregar_mensual_inserta_si_patente_no_existe(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = mensuales_controller.agregar_mensual("ABC123")

        self.assertTrue(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO vehiculos", consultas)

    @patch.object(mensuales_controller, "db_cursor")
    def test_eliminar_mensual_desactiva_vehiculo(self, db_cursor):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = mensuales_controller.eliminar_mensual(1)

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(commit=True)
        self.assertIn("UPDATE vehiculos SET activo = 0", cursor.executed[0][0])

    @patch.object(mensuales_controller, "db_cursor")
    def test_actualizar_tarifa_actualiza_tarifa_mensual(self, db_cursor):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = mensuales_controller.actualizar_tarifa(1, 50000)

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(commit=True)
        self.assertIn("UPDATE vehiculos SET tarifa_mensual", cursor.executed[0][0])


if __name__ == "__main__":
    unittest.main()
