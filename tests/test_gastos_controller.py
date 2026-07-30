import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from controllers import gastos_controller


class FakeCursor:
    def __init__(self, fetchall_result=None, fetchone_result=None, lastrowid=12):
        self.fetchall_result = fetchall_result or []
        self.fetchone_result = fetchone_result
        self.lastrowid = lastrowid
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        return self.fetchall_result

    def fetchone(self):
        return self.fetchone_result

    def close(self):
        pass


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class GastosControllerTests(unittest.TestCase):
    @patch.object(gastos_controller, "asegurar_schema_cierres")
    @patch.object(gastos_controller, "db_cursor")
    def test_registrar_gasto_valido_guarda_fecha_usuario_y_monto(self, db_cursor, asegurar_schema):
        cursor = FakeCursor(lastrowid=23)
        db_cursor.return_value = fake_db_cursor(cursor)

        gasto = gastos_controller.registrar_gasto("Insumos", "Jabón", "1500", "cajero")

        self.assertEqual(gasto["id_gasto"], 23)
        self.assertEqual(gasto["monto"], 1500)
        self.assertEqual(gasto["usuario"], "cajero")
        self.assertIsInstance(gasto["fecha_hora"], datetime)
        query, params = cursor.executed[0]
        self.assertIn("INSERT INTO gastos_operacion", query)
        self.assertEqual(params[1:], ("Insumos", "Jabón", 1500, "cajero"))
        asegurar_schema.assert_called_once_with()

    @patch.object(gastos_controller, "db_cursor")
    def test_registrar_gasto_valida_campos_y_no_accede_a_base(self, db_cursor):
        for args in (("", "Detalle", "100", "admin"), ("Otros", "", "100", "admin"), ("Otros", "Detalle", "0", "admin"), ("Otros", "Detalle", "100.5", "admin")):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    gastos_controller.registrar_gasto(*args)
        db_cursor.assert_not_called()

    @patch.object(gastos_controller, "asegurar_schema_cierres")
    @patch.object(gastos_controller, "db_cursor")
    def test_lista_pendientes_y_total(self, db_cursor, asegurar_schema):
        lista_cursor = FakeCursor(fetchall_result=[{"id_gasto": 1, "monto": 500}])
        total_cursor = FakeCursor(fetchone_result={"total": 500})
        db_cursor.side_effect = [fake_db_cursor(lista_cursor), fake_db_cursor(total_cursor)]

        gastos = gastos_controller.obtener_gastos_pendientes()
        total = gastos_controller.obtener_total_gastos_pendientes()

        self.assertEqual(gastos, [{"id_gasto": 1, "monto": 500}])
        self.assertEqual(total, 500)
        self.assertIn("WHERE id_cierre IS NULL", lista_cursor.executed[0][0])
        self.assertIn("WHERE id_cierre IS NULL", total_cursor.executed[0][0])
        self.assertEqual(asegurar_schema.call_count, 2)


if __name__ == "__main__":
    unittest.main()
