import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

import bcrypt

from controllers import login_controller


class FakeCursor:
    def __init__(self, fetchone_results=None):
        self.fetchone_results = list(fetchone_results or [])
        self.executed = []
        self.rowcount = 1

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class ValidarUsuarioTests(unittest.TestCase):
    @patch.object(login_controller, "registrar_asistencia_inicio")
    @patch.object(login_controller, "db_cursor")
    def test_retorna_inactivo_si_usuario_existe_pero_no_esta_activo(
        self,
        db_cursor,
        registrar_asistencia,
    ):
        cursor = FakeCursor(fetchone_results=[{"usuario": "admin", "activo": 0}])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = login_controller.validar_usuario("admin", "clave")

        self.assertEqual(resultado, ("inactivo", None))
        registrar_asistencia.assert_not_called()

    @patch.object(login_controller, "registrar_asistencia_inicio")
    @patch.object(login_controller, "cerrar_asistencias_activas")
    @patch.object(login_controller, "db_cursor")
    def test_retorna_true_y_rol_si_la_clave_es_correcta(self, db_cursor, cerrar_activas, registrar_asistencia):
        clave_hash = bcrypt.hashpw("secreta".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor = FakeCursor(
            fetchone_results=[
                {
                    "usuario": "admin",
                    "clave_hash": clave_hash,
                    "rol": "administrador",
                    "activo": 1,
                }
            ]
        )
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = login_controller.validar_usuario("admin", "secreta")

        self.assertEqual(resultado, (True, "administrador"))
        cerrar_activas.assert_called_once_with("admin")
        registrar_asistencia.assert_called_once_with("admin")

    @patch.object(login_controller, "registrar_asistencia_inicio")
    @patch.object(login_controller, "db_cursor")
    def test_retorna_false_si_la_clave_es_incorrecta(self, db_cursor, registrar_asistencia):
        clave_hash = bcrypt.hashpw("secreta".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor = FakeCursor(
            fetchone_results=[
                {
                    "usuario": "admin",
                    "clave_hash": clave_hash,
                    "rol": "administrador",
                    "activo": 1,
                }
            ]
        )
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = login_controller.validar_usuario("admin", "otra")

        self.assertEqual(resultado, (False, None))
        registrar_asistencia.assert_not_called()


class RegistrarAsistenciaSalidaTests(unittest.TestCase):
    @patch.object(login_controller, "db_cursor")
    def test_retorna_resumen_vacio_si_no_hay_asistencia_activa(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = fake_db_cursor(cursor)

        resumen = login_controller.registrar_asistencia_salida("admin")

        self.assertEqual(resumen, {"cantidad": 0, "total": 0, "hora_inicio": None})

    @patch.object(login_controller, "db_cursor")
    def test_cierra_asistencia_activa_con_totales_del_turno(self, db_cursor):
        hora_inicio = datetime(2026, 1, 1, 9, 0)
        cursor = FakeCursor(
            fetchone_results=[
                {"id_asistencia": 5, "hora_inicio": hora_inicio},
                {"cantidad": 3, "total": 4500},
                {"cantidad": 1, "total": 300},
            ]
        )
        db_cursor.return_value = fake_db_cursor(cursor)

        resumen = login_controller.registrar_asistencia_salida("admin")

        self.assertEqual(resumen, {"cantidad": 4, "total": 4800, "hora_inicio": hora_inicio})
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE asistencias", consultas)


if __name__ == "__main__":
    unittest.main()
