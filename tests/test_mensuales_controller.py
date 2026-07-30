import unittest
from contextlib import contextmanager
from datetime import datetime
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
    @patch.object(mensuales_controller, "asegurar_schema_mensuales")
    def test_obtener_mensuales_retorna_clientes_activos(self, asegurar_schema, db_cursor):
        mensuales = [{"id_vehiculo": 1, "patente": "ABC123", "tarifa_mensual": 50000, "dia_vencimiento": 10, "telefono": "1122334455"}]
        cursor = FakeCursor(fetchall_results=[mensuales])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = mensuales_controller.obtener_mensuales()

        self.assertEqual(resultado, mensuales)
        asegurar_schema.assert_called_once_with()
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
    def test_agregar_mensual_guarda_tarifa_vencimiento_y_telefono(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = fake_db_cursor(cursor)

        mensuales_controller.agregar_mensual("ABC123", 50000, 10, "1122334455")

        query, params = cursor.executed[-1]
        self.assertIn("tarifa_mensual, dia_vencimiento, telefono", query)
        self.assertEqual(params, ("ABC123", 50000, 10, "1122334455"))

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

    @patch.object(mensuales_controller, "db_cursor")
    def test_actualizar_tarifa_actualiza_vencimiento_y_telefono(self, db_cursor):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)

        mensuales_controller.actualizar_tarifa(1, 50000, 10, "1122334455")

        query, params = cursor.executed[0]
        self.assertIn("dia_vencimiento = %s, telefono = %s", query)
        self.assertEqual(params, (50000, 10, "1122334455", 1))

    def test_fecha_vencimiento_ajusta_los_dias_que_no_existen_en_el_mes(self):
        self.assertEqual(
            mensuales_controller.fecha_vencimiento_efectiva(datetime(2026, 2, 1), 31),
            datetime(2026, 2, 28),
        )

    def test_estado_pago_distingue_pendiente_vencido_y_pagado(self):
        periodo = datetime(2026, 2, 1)

        self.assertEqual(
            mensuales_controller.estado_pago_mensual(periodo, 31, False, datetime(2026, 2, 28, 10)),
            "pendiente",
        )
        self.assertEqual(
            mensuales_controller.estado_pago_mensual(periodo, 31, False, datetime(2026, 3, 1)),
            "vencido",
        )
        self.assertEqual(
            mensuales_controller.estado_pago_mensual(periodo, 1, True, datetime(2026, 2, 2)),
            "pagado",
        )

    @patch.object(mensuales_controller, "db_cursor")
    @patch.object(mensuales_controller, "asegurar_schema_mensuales")
    def test_registrar_pago_guarda_snapshots_del_periodo_actual(self, asegurar_schema, db_cursor):
        cursor = FakeCursor(fetchone_results=[{
            "id_vehiculo": 4,
            "tipo_cliente": "mensual",
            "activo": 1,
            "tarifa_mensual": 50000,
            "dia_vencimiento": 31,
        }, None])
        db_cursor.return_value = fake_db_cursor(cursor)
        ahora = datetime(2026, 2, 15, 11, 30)

        resultado = mensuales_controller.registrar_pago_mensual(4, "operador", "efectivo", "febrero", ahora)

        self.assertEqual(resultado, (True, "Pago mensual registrado."))
        asegurar_schema.assert_called_once_with()
        insercion = next((params for query, params in cursor.executed if "INSERT INTO pagos_mensuales" in query), None)
        self.assertEqual(insercion, (4, datetime(2026, 2, 1).date(), ahora, 50000, 31, "operador", "efectivo", "febrero"))

    @patch.object(mensuales_controller, "db_cursor")
    @patch.object(mensuales_controller, "asegurar_schema_mensuales")
    def test_registrar_pago_rechaza_duplicado_y_configuraciones_invalidas(self, asegurar_schema, db_cursor):
        duplicado = FakeCursor(fetchone_results=[{
            "id_vehiculo": 4,
            "tipo_cliente": "mensual",
            "activo": 1,
            "tarifa_mensual": 50000,
            "dia_vencimiento": 10,
        }, {"id_pago_mensual": 7}])
        db_cursor.return_value = fake_db_cursor(duplicado)

        self.assertEqual(
            mensuales_controller.registrar_pago_mensual(4, "operador", ahora=datetime(2026, 2, 15)),
            (False, "El período actual ya fue pagado."),
        )

        for vehiculo, mensaje in (
            ({"tipo_cliente": "ocasional", "activo": 1, "tarifa_mensual": 50000, "dia_vencimiento": 1}, "El vehículo no es un cliente mensual activo."),
            ({"tipo_cliente": "mensual", "activo": 0, "tarifa_mensual": 50000, "dia_vencimiento": 1}, "El vehículo no es un cliente mensual activo."),
            ({"tipo_cliente": "mensual", "activo": 1, "tarifa_mensual": 0, "dia_vencimiento": 1}, "La tarifa mensual debe ser mayor que cero."),
        ):
            cursor = FakeCursor(fetchone_results=[vehiculo])
            db_cursor.return_value = fake_db_cursor(cursor)
            self.assertEqual(
                mensuales_controller.registrar_pago_mensual(4, "operador", ahora=datetime(2026, 2, 15)),
                (False, mensaje),
            )


if __name__ == "__main__":
    unittest.main()
