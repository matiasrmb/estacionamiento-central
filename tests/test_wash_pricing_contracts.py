import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from controllers.wash_pricing_controller import (
    SOLO_LAVADO_PRICE_CONFIG_MESSAGE,
    build_wash_price_snapshot,
    build_wash_vehicle_type_payload,
    delete_wash_vehicle_type,
    ensure_wash_vehicle_type_table,
    list_wash_vehicle_types,
    resolve_wash_type_delete_action,
)
from controllers import wash_pricing_controller


class FakeCursor:
    def __init__(self, fetchall_results=None, scalar_results=None, rowcount=1):
        self.fetchall_results = list(fetchall_results or [])
        self.scalar_results = list(scalar_results or [])
        self.rowcount = rowcount
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []

    def fetchone(self):
        if self.scalar_results:
            return {"total": self.scalar_results.pop(0)}
        return {"total": 0}


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class WashPricingContractsTests(unittest.TestCase):
    def setUp(self):
        wash_pricing_controller._WASH_TYPES_ENSURED = False

    def test_active_type_snapshots_label_and_price(self):
        snapshot = build_wash_price_snapshot({
            "id_tipo_vehiculo_lavado": 7,
            "nombre": "SUV",
            "valor_lavado": "9000",
            "activo": 1,
        })

        self.assertEqual(snapshot, {
            "id_tipo_vehiculo_lavado": 7,
            "tipo_vehiculo_lavado_snapshot": "SUV",
            "valor_lavado_snapshot": 9000,
        })

    def test_inactive_type_cannot_create_new_snapshot(self):
        with self.assertRaises(ValueError):
            build_wash_price_snapshot({
                "id_tipo_vehiculo_lavado": 8,
                "nombre": "Furgon",
                "valor_lavado": 15000,
                "activo": 0,
            })

    def test_referenced_type_deactivates_instead_of_deleting(self):
        self.assertEqual(resolve_wash_type_delete_action(3), "deactivate")
        self.assertEqual(resolve_wash_type_delete_action(0), "delete")

    def test_schema_declares_additive_wash_pricing_tables_and_snapshots(self):
        schema = Path(__file__).resolve().parents[1].joinpath("schema.sql").read_text(encoding="utf-8")

        self.assertIn("CREATE TABLE IF NOT EXISTS tipos_lavado", schema)
        self.assertIn("CREATE TABLE IF NOT EXISTS tipos_vehiculo_lavado", schema)
        self.assertIn("id_tipo_vehiculo_lavado INT NULL", schema)
        self.assertIn("tipo_vehiculo_lavado_snapshot VARCHAR(80) DEFAULT NULL", schema)

    def test_config_payload_normalizes_label_price_and_active_state(self):
        payload = build_wash_vehicle_type_payload({
            "codigo": " suv ",
            "nombre": " SUV ",
            "valor_lavado": "9000",
            "activo": False,
        })

        self.assertEqual(payload, {
            "codigo": "suv",
            "nombre": "SUV",
            "valor_lavado": 9000,
            "activo": 0,
        })

    def test_config_payload_rejects_parking_tariff_fields(self):
        with self.assertRaises(ValueError) as ctx:
            build_wash_vehicle_type_payload({
                "codigo": "camioneta",
                "nombre": "Camioneta",
                "valor_lavado": 12000,
                "tarifa_hora": 5000,
            })

        self.assertEqual(str(ctx.exception), "PARKING_TARIFF_FIELDS_NOT_ALLOWED")

    @patch("controllers.wash_pricing_controller.db_cursor")
    def test_desktop_lists_wash_vehicle_types_without_parking_tariffs(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[{
            "clave": "lavado_suv",
            "valor": "9000",
        }], [{
            "id_tipo_vehiculo_lavado": 1,
            "codigo": "suv",
            "nombre": "SUV",
            "valor_lavado": 9000,
            "activo": 1,
        }]])
        db_cursor.side_effect = lambda **_: fake_db_cursor(cursor)

        items = list_wash_vehicle_types()

        self.assertEqual(items[0]["valor_lavado"], 9000)
        self.assertNotIn("tarifa_hora", items[0])

    @patch("controllers.wash_pricing_controller.db_cursor")
    def test_desktop_deactivates_referenced_wash_vehicle_type(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[]], scalar_results=[2], rowcount=1)
        db_cursor.side_effect = lambda **_: fake_db_cursor(cursor)

        action = delete_wash_vehicle_type(7)

        self.assertEqual(action, "deactivated")
        self.assertIn("UPDATE tipos_vehiculo_lavado", "\n".join(query for query, _ in cursor.executed))

    @patch("controllers.wash_pricing_controller.db_cursor")
    def test_ensure_wash_vehicle_type_table_seeds_legacy_config_and_copies_plural(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[{"clave": "lavado_citycar", "valor": "5000"}]])
        db_cursor.side_effect = lambda **_: fake_db_cursor(cursor)

        ensure_wash_vehicle_type_table()

        sql = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("CREATE TABLE IF NOT EXISTS tipos_vehiculo_lavado", sql)
        self.assertIn("FROM tipos_vehiculos_lavado", sql)
        self.assertIn("ON DUPLICATE KEY UPDATE", sql)

    @patch("controllers.wash_pricing_controller.db_cursor")
    def test_list_wash_vehicle_types_shows_clear_message_without_config(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[], []])
        db_cursor.side_effect = lambda **_: fake_db_cursor(cursor)

        with self.assertRaises(RuntimeError) as raised:
            list_wash_vehicle_types()

        self.assertEqual(str(raised.exception), SOLO_LAVADO_PRICE_CONFIG_MESSAGE)


if __name__ == "__main__":
    unittest.main()
