import unittest

from controllers.cotizaciones_controller import (
    calcular_minutos_estadia_por_horarios,
    cotizar_combinada,
    cotizar_estadia,
    cotizar_lavado,
    cotizar_mensualidad,
    preview_cotizacion,
    resolve_wash_quote_options,
    wash_quote_options_from_legacy_config,
)


class CotizacionesServiceTests(unittest.TestCase):
    def test_cotizar_estadia_ignora_tamano_vehiculo(self):
        citycar = cotizar_estadia(90, 2500, tamano_vehiculo="citycar")
        camioneta = cotizar_estadia(90, 2500, tamano_vehiculo="camioneta")

        self.assertEqual(citycar["monto"], 2500)
        self.assertEqual(camioneta["monto"], 2500)
        self.assertEqual(citycar, camioneta)

    def test_calcula_minutos_estadia_desde_horarios_concretos(self):
        minutos = calcular_minutos_estadia_por_horarios("13:00", "19:00")

        self.assertEqual(minutos, 360)

    def test_rechaza_horarios_invalidos_para_cotizar_estadia(self):
        casos_invalidos = [
            ("13", "19:00", "formato HH:MM"),
            ("13:60", "19:00", "válida"),
            ("13:00", "13:00", "distinta"),
            ("19:00", "13:00", "posterior"),
        ]

        for ingreso, salida, mensaje in casos_invalidos:
            with self.subTest(ingreso=ingreso, salida=salida):
                with self.assertRaisesRegex(ValueError, mensaje):
                    calcular_minutos_estadia_por_horarios(ingreso, salida)

    def test_cotizar_mensualidad_requiere_monto_faltante(self):
        cotizacion = cotizar_mensualidad([
            {"patente": "AAA111", "monto_mensual": None},
        ])

        self.assertTrue(cotizacion["requiere_monto"])
        self.assertIsNone(cotizacion["vehiculos"][0]["monto_mensual"])
        self.assertIsNone(cotizacion["vehiculos"][0]["costo_diario"])
        self.assertEqual(cotizacion["total_mensual"], 0)

    def test_cotizar_mensualidad_suma_varios_vehiculos(self):
        cotizacion = cotizar_mensualidad([
            {"patente": "AAA111", "monto_mensual": 60000},
            {"patente": "BBB222", "monto_configurado": 30000},
        ])

        self.assertFalse(cotizacion["requiere_monto"])
        self.assertEqual(cotizacion["total_mensual"], 90000)
        self.assertEqual(cotizacion["total_diario"], 3000)
        self.assertEqual(
            [vehiculo["costo_diario"] for vehiculo in cotizacion["vehiculos"]],
            [2000, 1000],
        )

    def test_cotizar_combinada_suma_previews_sin_efectos(self):
        estadia = cotizar_estadia(60, 2000, tamano_vehiculo="suv")
        lavado = cotizar_lavado("SUV", 8000)
        mensualidad = cotizar_mensualidad([{"patente": "AAA111", "monto_mensual": 30000}])

        cotizacion = cotizar_combinada(estadia, lavado, mensualidad)

        self.assertEqual(cotizacion["total"], 40000)
        self.assertEqual([item["tipo"] for item in cotizacion["items"]], ["estadia", "lavado", "mensualidad"])

    def test_wash_quote_options_fallback_uses_legacy_configured_prices(self):
        opciones = wash_quote_options_from_legacy_config({
            "lavado_citycar": "5000",
            "lavado_suv": "0",
            "lavado_camioneta": "10000",
        })

        self.assertEqual(
            [(item["codigo"], item["valor_lavado"], item["source"]) for item in opciones],
            [
                ("lavado_citycar", 5000, "legacy_configuracion"),
                ("lavado_camioneta", 10000, "legacy_configuracion"),
                ("lavado_furgon", 15000, "legacy_configuracion"),
                ("lavado_minibus", 25000, "legacy_configuracion"),
            ],
        )

    def test_resolve_wash_quote_options_falls_back_when_new_table_has_no_active_prices(self):
        opciones = resolve_wash_quote_options(
            [{"codigo": "suv", "nombre": "SUV", "valor_lavado": 8000, "activo": 0}],
            {"lavado_citycar": "5000"},
        )

        self.assertEqual(opciones[0]["codigo"], "lavado_citycar")
        self.assertEqual(opciones[0]["valor_lavado"], 5000)
        self.assertEqual(opciones[0]["source"], "legacy_configuracion")

    def test_preview_mensualidad_accepts_manual_amount_without_persistence(self):
        cotizacion = preview_cotizacion({
            "mensualidad": {"vehiculos": [{"patente": "MENSUAL", "monto_mensual": 90000}]}
        })

        self.assertEqual(cotizacion["total"], 90000)
        self.assertEqual(cotizacion["items"][0]["total_diario"], 3000)


if __name__ == "__main__":
    unittest.main()
