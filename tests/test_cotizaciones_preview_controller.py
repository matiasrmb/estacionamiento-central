import unittest

from controllers import cotizaciones_controller


class CotizacionesPreviewControllerTests(unittest.TestCase):
    def test_preview_combines_requested_items_without_side_effects(self):
        cotizacion = cotizaciones_controller.preview_cotizacion({
            "estadia": {"minutos": 90, "monto_estadia": 2500, "tamano_vehiculo": "camioneta"},
            "lavado": {"tipo_lavado": "Completo", "monto_lavado": 8000},
            "mensualidad": {
                "vehiculos": [
                    {"patente": "AAA111", "monto_mensual": 60000},
                    {"patente": "BBB222", "monto_configurado": 30000},
                ]
            },
        })

        self.assertEqual(cotizacion["tipo"], "combinada")
        self.assertEqual(cotizacion["total"], 100500)
        self.assertEqual([item["tipo"] for item in cotizacion["items"]], ["estadia", "lavado", "mensualidad"])
        self.assertEqual(cotizacion["items"][2]["total_mensual"], 90000)
        self.assertEqual(cotizacion["items"][2]["total_diario"], 3000)
        self.assertFalse(cotizacion["creates_billable_rows"])

    def test_preview_requires_monthly_amount_for_each_vehicle(self):
        with self.assertRaisesRegex(ValueError, "MONTHLY_AMOUNT_REQUIRED"):
            cotizaciones_controller.preview_cotizacion({
                "mensualidad": {"vehiculos": [{"patente": "SINMONTO", "monto_mensual": None}]}
            })


if __name__ == "__main__":
    unittest.main()
