import unittest
from contextlib import contextmanager
from datetime import date, datetime, time
from unittest.mock import Mock, patch

from controllers import reportes_controller


class FakeCursor:
    def __init__(self, fetchall_results=None, fetchone_results=None):
        self.fetchall_results = list(fetchall_results or [])
        self.fetchone_results = list(fetchone_results or [])
        self.executed = []

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


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class ObtenerReportesTests(unittest.TestCase):
    @patch.object(reportes_controller, "db_cursor")
    def test_obtener_reportes_incluye_banos_si_no_filtra_patente(self, db_cursor):
        movimiento = {
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "fecha_hora_salida": datetime(2026, 1, 1, 11, 0),
            "minutos": 60,
            "tarifa_aplicada": 1200,
        }
        bano = {
            "fecha_hora": datetime(2026, 1, 1, 12, 0),
            "monto": 300,
            "usuario": "admin",
        }
        pago_mensual = {
            "patente": "MENSUAL1",
            "periodo": date(2026, 1, 1),
            "fecha_pago": datetime(2026, 1, 15, 10, 0),
            "monto_snapshot": 50000,
        }
        cobro_noche = {
            "patente": "ABC123",
            "fecha_hora_pago": datetime(2026, 1, 2, 22, 0),
            "monto_snapshot": 5000,
        }
        cursor = FakeCursor(fetchall_results=[
            [movimiento], [bano], [], [], [pago_mensual], [cobro_noche],
        ])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = reportes_controller.obtener_reportes(date(2026, 1, 1), date(2026, 1, 31))

        self.assertEqual(len(resultado), 4)
        self.assertEqual(resultado[1]["patente"], "[BAÑO]")
        self.assertEqual(resultado[1]["tarifa_aplicada"], 300)
        mensualidad = next(item for item in resultado if item.get("tipo") == "mensualidad")
        noche = next(item for item in resultado if item.get("tipo") == "noche")
        self.assertEqual(mensualidad["patente"], "[MENSUAL] MENSUAL1")
        self.assertEqual(mensualidad["tarifa_aplicada"], 50000)
        self.assertEqual(noche["patente"], "[NOCHES] ABC123")
        self.assertEqual(len(cursor.executed), 6)
        self.assertIn("FROM ingresos_eliminados", cursor.executed[0][0])
        self.assertIn("id_ingreso_generado IS NULL", cursor.executed[2][0])

    @patch.object(reportes_controller, "db_cursor")
    def test_obtener_reportes_filtra_por_patente_y_no_incluye_banos(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[], [], [], []])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = reportes_controller.obtener_reportes(
            date(2026, 1, 1),
            date(2026, 1, 31),
            patente="ABC123",
        )

        self.assertEqual(resultado, [])
        self.assertEqual(len(cursor.executed), 4)
        self.assertIn("AND v.patente = %s", cursor.executed[0][0])
        self.assertIn("WHERE patente = %s", cursor.executed[1][0])
        self.assertIn("id_ingreso_generado IS NULL", cursor.executed[1][0])
        self.assertIn("AND v.patente = %s", cursor.executed[2][0])
        self.assertIn("AND v.patente = %s", cursor.executed[3][0])
        self.assertEqual(
            cursor.executed[0][1],
            (date(2026, 1, 1), date(2026, 1, 31), "ABC123"),
        )
        self.assertEqual(
            cursor.executed[1][1],
            ("ABC123", date(2026, 1, 1), date(2026, 1, 31)),
        )
        for _, params in cursor.executed[2:]:
            self.assertEqual(params, (date(2026, 1, 1), date(2026, 1, 31), "ABC123"))

    @patch.object(reportes_controller, "db_cursor")
    def test_obtener_reportes_filters_plate_time_and_user_across_categories(self, db_cursor):
        parking = {
            "tipo": "vehiculo",
            "categoria": "Vehículo",
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 10, 9, 0),
            "fecha_hora_salida": datetime(2026, 1, 10, 11, 30),
            "minutos": 150,
            "tarifa_aplicada": 4000,
            "usuario": "admin",
        }
        wash = {
            "tipo": "lavado_solo",
            "categoria": "Lavado solo",
            "patente": "ABC123",
            "fecha_hora_inicio": datetime(2026, 1, 10, 10, 0),
            "fecha_hora_fin": datetime(2026, 1, 10, 12, 0),
            "minutos": 120,
            "valor_lavado_snapshot": 8000,
            "usuario": "admin",
        }
        monthly = {
            "tipo": "mensualidad",
            "categoria": "Mensualidad",
            "patente": "ABC123",
            "periodo": date(2026, 1, 1),
            "fecha_pago": datetime(2026, 1, 10, 12, 30),
            "monto_snapshot": 50000,
            "usuario": "admin",
        }
        night = {
            "tipo": "noche",
            "categoria": "Noche",
            "patente": "ABC123",
            "fecha_hora_pago": datetime(2026, 1, 10, 13, 0),
            "monto_snapshot": 5000,
            "usuario": "admin",
        }
        cursor = FakeCursor(fetchall_results=[[parking], [wash], [monthly], [night]])
        db_cursor.return_value = fake_db_cursor(cursor)

        payload = reportes_controller.obtener_reportes(
            date(2026, 1, 10),
            date(2026, 1, 10),
            patente="ABC123",
            hora_inicio=time(10, 0),
            hora_fin=time(13, 0),
            usuario="admin",
        )

        self.assertIsInstance(payload, dict)
        self.assertIn("items", payload)
        self.assertIn("totals", payload)
        self.assertEqual(
            [item["tipo"] for item in payload["items"]],
            ["vehiculo", "lavado_solo", "mensualidad", "noche"],
        )
        self.assertEqual({item["patente"] for item in payload["items"]}, {"ABC123"})
        self.assertTrue(
            all(time(10, 0) <= item["fecha_hora_salida"].time() <= time(13, 0) for item in payload["items"])
        )
        self.assertEqual({item["usuario"] for item in payload["items"]}, {"admin"})
        self.assertNotIn("bano", {item["tipo"] for item in payload["items"]})
        self.assertNotIn("gasto", {item["tipo"] for item in payload["items"]})

    @patch.object(reportes_controller, "db_cursor")
    def test_obtener_reportes_returns_category_labels_and_user_context(self, db_cursor):
        parking = {
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 10, 9, 0),
            "fecha_hora_salida": datetime(2026, 1, 10, 10, 0),
            "minutos": 60,
            "tarifa_aplicada": 3000,
            "usuario": "cashier",
        }
        bathroom = {
            "fecha_hora": datetime(2026, 1, 10, 10, 30),
            "monto": 300,
            "usuario": "cashier",
        }
        wash = {
            "patente": "WASH1",
            "fecha_hora_inicio": datetime(2026, 1, 10, 11, 0),
            "fecha_hora_fin": datetime(2026, 1, 10, 12, 0),
            "minutos": 60,
            "valor_lavado_snapshot": 8000,
            "usuario_fin": "washer",
        }
        expense = {
            "fecha_hora": datetime(2026, 1, 10, 12, 30),
            "monto": 1500,
            "descripcion": "Supplies",
            "usuario": "manager",
        }
        monthly = {
            "patente": "MONTH1",
            "periodo": date(2026, 1, 1),
            "fecha_pago": datetime(2026, 1, 10, 13, 0),
            "monto_snapshot": 50000,
            "usuario": "cashier",
        }
        night = {
            "patente": "NIGHT1",
            "fecha_hora_pago": datetime(2026, 1, 10, 14, 0),
            "monto_snapshot": 5000,
            "usuario": "cashier",
        }
        cursor = FakeCursor(fetchall_results=[
            [parking], [bathroom], [wash], [expense], [monthly], [night],
        ])
        db_cursor.return_value = fake_db_cursor(cursor)

        payload = reportes_controller.obtener_reportes(date(2026, 1, 10), date(2026, 1, 10))

        self.assertIsInstance(payload, dict)
        items_by_type = {item["tipo"]: item for item in payload["items"]}
        self.assertEqual(items_by_type["vehiculo"]["categoria"], "Vehículo")
        self.assertEqual(items_by_type["bano"]["categoria"], "Baño")
        self.assertEqual(items_by_type["lavado_solo"]["categoria"], "Lavado solo")
        self.assertEqual(items_by_type["mensualidad"]["categoria"], "Mensualidad")
        self.assertEqual(items_by_type["noche"]["categoria"], "Noche")
        self.assertEqual(items_by_type["gasto"]["categoria"], "Gasto")
        self.assertEqual(items_by_type["vehiculo"]["usuario"], "cashier")
        self.assertEqual(items_by_type["lavado_solo"]["usuario"], "washer")
        self.assertEqual(items_by_type["gasto"]["usuario"], "manager")

    @patch.object(reportes_controller, "db_cursor")
    def test_obtener_reportes_returns_explicit_empty_payload_when_no_rows_match(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[], [], [], [], [], []])
        db_cursor.return_value = fake_db_cursor(cursor)

        payload = reportes_controller.obtener_reportes(date(2026, 1, 10), date(2026, 1, 10))

        self.assertEqual(payload["items"], [])
        self.assertEqual(payload["totals"]["total_recaudado"], 0)
        self.assertEqual(payload["totals"]["total_banos_monto"], 0)
        self.assertEqual(payload["totals"]["total_lavados_solos_monto"], 0)
        self.assertEqual(payload["totals"]["total_mensualidades_monto"], 0)
        self.assertEqual(payload["totals"]["total_noches_monto"], 0)
        self.assertEqual(payload["totals"]["total_gastos"], 0)
        self.assertEqual(payload["totals"]["total_general"], 0)
        self.assertEqual(payload["totals"]["total_neto"], 0)
        self.assertEqual(payload["totals"]["total_movimientos"], 0)


class ExportarPdfTests(unittest.TestCase):
    @patch.object(reportes_controller, "abrir_pdf")
    @patch.object(reportes_controller, "os")
    @patch.object(reportes_controller, "ReportePDF")
    @patch.object(reportes_controller, "db_cursor")
    def test_exportar_pdf_consulta_totales_banos_si_se_incluyen(
        self,
        db_cursor,
        reporte_pdf,
        os_mock,
        abrir_pdf,
    ):
        cursor = FakeCursor(fetchone_results=[
            {"cantidad": 2, "total": 600},
            {"cantidad": 1, "total": 50000},
            {"cantidad": 1, "total": 5000},
        ])
        db_cursor.return_value = fake_db_cursor(cursor)
        pdf = Mock()
        reporte_pdf.return_value = pdf
        os_mock.path.join.return_value = "reportes/reporte.pdf"

        datos = [
            {
                "patente": "ABC123",
                "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
                "fecha_hora_salida": datetime(2026, 1, 1, 11, 0),
                "tarifa_aplicada": 1200,
            }
        ]

        reportes_controller.exportar_pdf(
            datos,
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 1, 31),
            incluir_banos=True,
        )

        db_cursor.assert_called_once_with(dictionary=True)
        self.assertIn(
            "Mensualidades cobradas: 1",
            [call.args[2] for call in pdf.cell.call_args_list],
        )
        self.assertIn(
            "Total recaudado por mensualidades: $50000",
            [call.args[2] for call in pdf.cell.call_args_list],
        )
        self.assertIn("Total neto: $1200", [call.args[2] for call in pdf.cell.call_args_list])
        self.assertIn(
            "Total recaudado por Noches prepagadas: $5000",
            [call.args[2] for call in pdf.cell.call_args_list],
        )
        pdf.output.assert_called_once_with("reportes/reporte.pdf")
        abrir_pdf.assert_called_once_with("reportes/reporte.pdf")

    @patch.object(reportes_controller, "abrir_pdf")
    @patch.object(reportes_controller, "os")
    @patch.object(reportes_controller, "ReportePDF")
    @patch.object(reportes_controller, "db_cursor")
    def test_exportar_pdf_filtra_total_mensual_por_patente_y_fecha(
        self,
        db_cursor,
        reporte_pdf,
        os_mock,
        abrir_pdf,
    ):
        cursor = FakeCursor(fetchone_results=[
            {"cantidad": 1, "total": 50000},
            {"cantidad": 0, "total": 0},
        ])
        db_cursor.return_value = fake_db_cursor(cursor)
        reporte_pdf.return_value = Mock()
        os_mock.path.join.return_value = "reportes/reporte.pdf"

        reportes_controller.exportar_pdf(
            [],
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 1, 31),
            patente="ABC123",
        )

        self.assertEqual(len(cursor.executed), 2)
        query, params = cursor.executed[0]
        self.assertIn("FROM pagos_mensuales", query)
        self.assertIn("AND v.patente = %s", query)
        self.assertEqual(params, (date(2026, 1, 1), date(2026, 1, 31), "ABC123"))


if __name__ == "__main__":
    unittest.main()
