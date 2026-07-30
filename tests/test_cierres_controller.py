import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from controllers import cierres_controller


class FakeCursor:
    def __init__(self, fetchall_results=None, fetchone_results=None, lastrowid=71):
        self.fetchall_results = list(fetchall_results or [])
        self.fetchone_results = list(fetchone_results or [])
        self.executed = []
        self.lastrowid = lastrowid

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        return self.fetchall_results.pop(0) if self.fetchall_results else []

    def fetchone(self):
        return self.fetchone_results.pop(0) if self.fetchone_results else None

    def close(self):
        pass


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class RealizarCierreDiarioTests(unittest.TestCase):
    def test_schema_declara_vinculos_y_totales_canonicos_de_cierre(self):
        with open("schema.sql", encoding="utf-8") as schema_file:
            schema = schema_file.read()

        self.assertIn("CREATE TABLE IF NOT EXISTS gastos_operacion", schema)
        self.assertIn("total_gastos INT NOT NULL DEFAULT 0", schema)
        self.assertIn("total_neto INT NOT NULL DEFAULT 0", schema)
        self.assertIn("id_cierre INT NULL", schema)

    @patch.object(cierres_controller, "asegurar_schema_cierres")
    @patch.object(cierres_controller, "generar_pdf_cierre")
    @patch.object(cierres_controller, "db_cursor")
    def test_retorna_false_si_no_hay_registros_pendientes(self, db_cursor, generar_pdf, asegurar_schema):
        cursor = FakeCursor(fetchall_results=[[], [], [], []], fetchone_results=[None])
        db_cursor.return_value = fake_db_cursor(cursor)

        exito, mensaje = cierres_controller.realizar_cierre_diario("admin")

        self.assertFalse(exito)
        self.assertEqual(mensaje, "No hay registros para cerrar hoy.")
        asegurar_schema.assert_called_once_with()
        generar_pdf.assert_not_called()

    @patch.object(cierres_controller, "asegurar_schema_cierres")
    @patch.object(cierres_controller, "generar_pdf_cierre")
    @patch.object(cierres_controller, "db_cursor")
    def test_cierre_mixto_calcula_bruto_gastos_neto_y_vincula_pendientes(
        self, db_cursor, generar_pdf, asegurar_schema
    ):
        registros = [{
            "id_ingreso": 1,
            "fecha_hora_ingreso": datetime(2026, 1, 1, 9, 0),
            "fecha_hora_salida": datetime(2026, 1, 1, 10, 0),
            "tarifa_aplicada": 1000,
        }]
        cursor = FakeCursor(
            fetchall_results=[
                registros,
                [{"id": 3, "monto": 600}],
                [{"id_operacion_servicio": 4, "valor_lavado_snapshot": 8000}],
                [{"id_gasto": 5, "monto": 2300}],
            ],
            fetchone_results=[None],
            lastrowid=44,
        )
        db_cursor.return_value = fake_db_cursor(cursor)

        exito, mensaje = cierres_controller.realizar_cierre_diario("admin")

        self.assertTrue(exito)
        self.assertIn("$7300", mensaje)
        asegurar_schema.assert_called_once_with()
        generar_pdf.assert_called_once()
        datos_pdf = generar_pdf.call_args.args[1]
        self.assertEqual(datos_pdf["Total general bruto"], "$9600")
        self.assertEqual(datos_pdf["Total gastos"], "$2300")
        self.assertEqual(datos_pdf["Total neto del día"], "$7300")

        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO cierres_diarios", consultas)
        self.assertIn("UPDATE ingresos SET cerrado = TRUE", consultas)
        self.assertIn("UPDATE usos_bano SET id_cierre = %s", consultas)
        self.assertIn("UPDATE operaciones_servicio SET cerrado = TRUE", consultas)
        self.assertIn("UPDATE gastos_operacion SET id_cierre = %s", consultas)

    @patch.object(cierres_controller, "asegurar_schema_cierres")
    @patch.object(cierres_controller, "generar_pdf_cierre")
    @patch.object(cierres_controller, "db_cursor")
    def test_cierre_solo_con_gastos_es_valido_y_los_vincula(
        self, db_cursor, generar_pdf, asegurar_schema
    ):
        cursor = FakeCursor(
            fetchall_results=[[], [], [], [{"id_gasto": 9, "monto": 1200}]],
            fetchone_results=[None],
            lastrowid=99,
        )
        db_cursor.return_value = fake_db_cursor(cursor)

        exito, mensaje = cierres_controller.realizar_cierre_diario("admin")

        self.assertTrue(exito)
        self.assertIn("$-1200", mensaje)
        datos_pdf = generar_pdf.call_args.args[1]
        self.assertEqual(datos_pdf["Total general bruto"], "$0")
        self.assertEqual(datos_pdf["Total gastos"], "$1200")
        self.assertEqual(datos_pdf["Total neto del día"], "$-1200")
        update = next((params for query, params in cursor.executed if "UPDATE gastos_operacion" in query), None)
        self.assertEqual(update, [99, 9])

    @patch.object(cierres_controller, "asegurar_schema_cierres")
    @patch.object(cierres_controller, "generar_pdf_cierre")
    @patch.object(cierres_controller, "db_cursor")
    def test_gasto_ya_vinculado_no_se_incluye_en_siguiente_cierre(
        self, db_cursor, generar_pdf, asegurar_schema
    ):
        cursor = FakeCursor(fetchall_results=[[], [], [], []], fetchone_results=[None])
        db_cursor.return_value = fake_db_cursor(cursor)

        exito, _ = cierres_controller.realizar_cierre_diario("admin")

        self.assertFalse(exito)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM gastos_operacion\n            WHERE id_cierre IS NULL", consultas)
        self.assertNotIn("UPDATE gastos_operacion SET id_cierre", consultas)


if __name__ == "__main__":
    unittest.main()
