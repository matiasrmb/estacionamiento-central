import unittest
from pathlib import Path


class AsistenciasSchemaContractTests(unittest.TestCase):
    def test_schema_declares_managed_010_asistencias_contract(self):
        schema = Path(__file__).resolve().parents[1].joinpath("schema.sql").read_text(encoding="utf-8")

        self.assertIn("CREATE TABLE IF NOT EXISTS asistencias", schema)
        self.assertIn("device_id VARCHAR(128) NULL", schema)
        self.assertIn("session_id VARCHAR(64) NULL", schema)
        self.assertIn(
            "INDEX idx_asistencias_sesion_activa (usuario, session_id, hora_salida)",
            schema,
        )


if __name__ == "__main__":
    unittest.main()
