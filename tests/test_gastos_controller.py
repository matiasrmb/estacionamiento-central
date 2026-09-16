import unittest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
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
    def test_gastos_no_repara_schema_en_runtime(self):
        source = Path("controllers/gastos_controller.py").read_text(encoding="utf-8")

        self.assertNotIn("asegurar_schema_cierres", source)

    @patch.object(gastos_controller, "db_cursor")
    def test_registrar_gasto_valido_guarda_fecha_usuario_y_monto(self, db_cursor):
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

    @patch.object(gastos_controller, "db_cursor")
    def test_registrar_gasto_valida_campos_y_no_accede_a_base(self, db_cursor):
        for args in (("", "Detalle", "100", "admin"), ("Otros", "", "100", "admin"), ("Otros", "Detalle", "0", "admin"), ("Otros", "Detalle", "100.5", "admin")):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    gastos_controller.registrar_gasto(*args)
        db_cursor.assert_not_called()

    @patch.object(gastos_controller, "db_cursor")
    def test_lista_pendientes_y_total(self, db_cursor):
        lista_cursor = FakeCursor(fetchall_result=[{"id_gasto": 1, "monto": 500}])
        total_cursor = FakeCursor(fetchone_result={"total": 500})
        db_cursor.side_effect = [fake_db_cursor(lista_cursor), fake_db_cursor(total_cursor)]

        gastos = gastos_controller.obtener_gastos_pendientes()
        total = gastos_controller.obtener_total_gastos_pendientes()

        self.assertEqual(gastos, [{"id_gasto": 1, "monto": 500}])
        self.assertEqual(total, 500)
        self.assertIn("WHERE id_cierre IS NULL", lista_cursor.executed[0][0])
        self.assertIn("WHERE id_cierre IS NULL", total_cursor.executed[0][0])

    @patch.object(gastos_controller, "db_cursor")
    def test_admin_edita_gasto_pendiente_con_auditoria(self, db_cursor):
        cursor = FakeCursor(fetchone_result={
            "id_gasto": 9,
            "fecha_hora": datetime(2026, 7, 1, 10, 0),
            "categoria": "Insumos",
            "descripcion": "Agua",
            "monto": 250,
            "usuario": "operador",
            "id_cierre": None,
        })
        db_cursor.return_value = fake_db_cursor(cursor)

        gasto = gastos_controller.editar_gasto(9, "Servicios", "Luz", "500", "admin", "administrador")

        sql = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FOR UPDATE", sql)
        self.assertIn("UPDATE gastos_operacion", sql)
        self.assertIn("INSERT INTO gastos_operacion_auditoria", sql)
        self.assertEqual(gasto["categoria"], "Servicios")
        self.assertIn('"categoria": "Insumos"', cursor.executed[-1][1][4])
        self.assertIn('"categoria": "Servicios"', cursor.executed[-1][1][5])

    @patch.object(gastos_controller, "db_cursor")
    def test_admin_elimina_gasto_pendiente_con_auditoria(self, db_cursor):
        cursor = FakeCursor(fetchone_result={
            "id_gasto": 9,
            "fecha_hora": datetime(2026, 7, 1, 10, 0),
            "categoria": "Insumos",
            "descripcion": "Agua",
            "monto": 250,
            "usuario": "operador",
            "id_cierre": None,
        })
        db_cursor.return_value = fake_db_cursor(cursor)

        result = gastos_controller.eliminar_gasto(9, "admin", "admin")

        sql = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("DELETE FROM gastos_operacion", sql)
        self.assertIn("INSERT INTO gastos_operacion_auditoria", sql)
        self.assertEqual(result, {"ok": True, "id_gasto": 9})
        self.assertIn('"id_gasto": 9', cursor.executed[-1][1][4])
        self.assertIsNone(cursor.executed[-1][1][5])

    @patch.object(gastos_controller, "db_cursor")
    def test_operador_no_edita_ni_elimina_y_no_accede_a_base(self, db_cursor):
        with self.assertRaises(PermissionError):
            gastos_controller.editar_gasto(9, "Servicios", "Luz", "500", "operador", "operador")
        with self.assertRaises(PermissionError):
            gastos_controller.eliminar_gasto(9, "operador", "operador")
        db_cursor.assert_not_called()

    @patch.object(gastos_controller, "db_cursor")
    def test_rechaza_editar_o_eliminar_gasto_cerrado(self, db_cursor):
        closed = {
            "id_gasto": 9,
            "fecha_hora": datetime(2026, 7, 1, 10, 0),
            "categoria": "Insumos",
            "descripcion": "Agua",
            "monto": 250,
            "usuario": "operador",
            "id_cierre": 3,
        }
        for action in (
            lambda: gastos_controller.editar_gasto(9, "Servicios", "Luz", "500", "admin", "admin"),
            lambda: gastos_controller.eliminar_gasto(9, "admin", "admin"),
        ):
            cursor = FakeCursor(fetchone_result=closed)
            db_cursor.return_value = fake_db_cursor(cursor)
            with self.subTest(action=action), self.assertRaises(ValueError):
                action()
            sql = "\n".join(query for query, _ in cursor.executed)
            self.assertNotIn("UPDATE gastos_operacion", sql)
            self.assertNotIn("DELETE FROM gastos_operacion", sql)


if __name__ == "__main__":
    unittest.main()
