import unittest
from contextlib import contextmanager
from unittest.mock import patch

from controllers import usuarios_controller


class FakeCursor:
    def __init__(self, fetchone_results=None, rowcount=1, missing_tables=None):
        self.fetchone_results = list(fetchone_results or [])
        self.executed = []
        self.rowcount = rowcount
        self.missing_tables = set(missing_tables or [])

    def execute(self, query, params=None):
        self.executed.append((query, params))
        for table in self.missing_tables:
            if f"FROM {table}" in query:
                raise RuntimeError(f"Table 'estacionamiento.{table}' doesn't exist")

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class UsuariosControllerSafeDeleteTests(unittest.TestCase):
    @patch.object(usuarios_controller, "db_cursor")
    def test_eliminar_usuario_sin_actividad_hace_hard_delete(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[
            {"usuario": "nuevo", "rol": "operador", "activo": 1},
            None, None, None, None, None, None, None, None,
        ])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = usuarios_controller.eliminar_usuario_seguro("nuevo", usuario_actual="admin")

        self.assertEqual(resultado["action"], "deleted")
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("DELETE FROM usuarios", consultas)

    @patch.object(usuarios_controller, "db_cursor")
    def test_eliminar_usuario_sin_actividad_ignora_tablas_opcionales_faltantes(self, db_cursor):
        cursor = FakeCursor(
            fetchone_results=[
                {"usuario": "nuevo", "rol": "operador", "activo": 1},
                None, None, None, None, None,
            ],
            missing_tables={"operaciones_servicio", "ingresos_eliminados", "print_jobs"},
        )
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = usuarios_controller.eliminar_usuario_seguro("nuevo", usuario_actual="admin")

        self.assertEqual(resultado, {"ok": True, "action": "deleted", "message": "USER_DELETED"})
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM ingresos", consultas)
        self.assertIn("DELETE FROM usuarios", consultas)

    @patch.object(usuarios_controller, "db_cursor")
    def test_eliminar_usuario_con_actividad_desactiva_y_preserva_historial(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[
            {"usuario": "operador", "rol": "operador", "activo": 1},
            {"found": 1},
        ])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = usuarios_controller.eliminar_usuario_seguro("operador", usuario_actual="admin")

        self.assertEqual(resultado["action"], "deactivated")
        self.assertEqual(resultado["message"], "USER_DEACTIVATED_HISTORY_PRESERVED")
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE usuarios SET activo", consultas)
        self.assertNotIn("DELETE FROM usuarios", consultas)

    def test_error_interno_de_eliminacion_no_se_muestra_como_bloqueo_por_historial(self):
        from views.usuarios import formatear_error_eliminacion

        titulo, mensaje, severidad = formatear_error_eliminacion({"message": "USER_DELETE_ERROR"})

        self.assertEqual(titulo, "Error interno")
        self.assertEqual(severidad, "critical")
        self.assertIn("revisá los logs", mensaje.lower())

    @patch.object(usuarios_controller, "db_cursor")
    def test_bloquea_eliminar_usuario_actual(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[{"usuario": "admin", "rol": "administrador", "activo": 1}])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = usuarios_controller.eliminar_usuario_seguro("admin", usuario_actual="admin")

        self.assertEqual(resultado["action"], "blocked")
        self.assertEqual(resultado["message"], "CANNOT_DELETE_CURRENT_USER")

    @patch.object(usuarios_controller, "db_cursor")
    def test_bloquea_eliminar_ultimo_admin_activo(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[
            {"usuario": "admin2", "rol": "administrador", "activo": 1},
            {"active_admins_after_delete": 0},
        ])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = usuarios_controller.eliminar_usuario_seguro("admin2", usuario_actual="admin")

        self.assertEqual(resultado["action"], "blocked")
        self.assertEqual(resultado["message"], "CANNOT_DELETE_LAST_ADMIN")


if __name__ == "__main__":
    unittest.main()
