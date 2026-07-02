import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from controllers.wash_pricing_controller import (
    build_wash_price_snapshot,
    build_wash_vehicle_type_payload,
    delete_wash_vehicle_type,
    list_wash_vehicle_types,
    resolve_wash_type_delete_action,
)


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
            "id_tipo_vehiculo_lavado": 1,
            "codigo": "suv",
            "nombre": "SUV",
            "valor_lavado": 9000,
            "activo": 1,
        }]])
        db_cursor.return_value = fake_db_cursor(cursor)

        items = list_wash_vehicle_types()

        self.assertEqual(items[0]["valor_lavado"], 9000)
        self.assertNotIn("tarifa_hora", items[0])

    @patch("controllers.wash_pricing_controller.db_cursor")
    def test_desktop_deactivates_referenced_wash_vehicle_type(self, db_cursor):
        cursor = FakeCursor(scalar_results=[2], rowcount=1)
        db_cursor.return_value = fake_db_cursor(cursor)

        action = delete_wash_vehicle_type(7)

        self.assertEqual(action, "deactivated")
        self.assertIn("UPDATE tipos_vehiculo_lavado", cursor.executed[1][0])


if __name__ == "__main__":
    unittest.main()
