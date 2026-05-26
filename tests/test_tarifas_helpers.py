import unittest
from datetime import datetime
from unittest.mock import patch

from controllers import tarifas_controller
from controllers.tarifas_controller import (
    calcular_tarifa,
    calcular_tarifa_con_contexto,
    construir_intervalos_equitativos,
    construir_valores_automaticos,
    obtener_contexto_tarifa,
)


class ConstruirValoresAutomaticosTests(unittest.TestCase):
    def test_genera_valores_cada_100_incluyendo_extremos(self):
        self.assertEqual(
            construir_valores_automaticos(300, 600),
            [300, 400, 500, 600],
        )

    def test_permite_tarifa_minima_igual_a_tarifa_hora(self):
        self.assertEqual(construir_valores_automaticos(500, 500), [500])

    def test_rechaza_valores_no_positivos(self):
        with self.assertRaises(ValueError):
            construir_valores_automaticos(0, 500)

        with self.assertRaises(ValueError):
            construir_valores_automaticos(300, 0)

    def test_rechaza_tarifa_hora_menor_que_minima(self):
        with self.assertRaises(ValueError):
            construir_valores_automaticos(700, 500)

    def test_rechaza_diferencia_que_no_es_multiplo_de_100(self):
        with self.assertRaises(ValueError):
            construir_valores_automaticos(300, 650)


class ConstruirIntervalosEquitativosTests(unittest.TestCase):
    def test_distribuye_intervalos_equitativos(self):
        self.assertEqual(
            construir_intervalos_equitativos(4, 8),
            [(0, 1), (2, 3), (4, 5), (6, 7)],
        )

    def test_distribuye_sobrantes_en_los_primeros_intervalos(self):
        self.assertEqual(
            construir_intervalos_equitativos(3, 10),
            [(0, 3), (4, 6), (7, 9)],
        )

    def test_rechaza_cantidad_no_positiva(self):
        with self.assertRaises(ValueError):
            construir_intervalos_equitativos(0, 60)

    def test_rechaza_mas_tramos_que_minutos(self):
        with self.assertRaises(ValueError):
            construir_intervalos_equitativos(61, 60)


class TarifaContextoTests(unittest.TestCase):
    @patch.object(tarifas_controller, "obtener_tarifas_personalizadas")
    @patch.object(tarifas_controller, "obtener_subida_activa")
    @patch.object(tarifas_controller, "obtener_configuracion")
    def test_obtener_contexto_tarifa_carga_tramos_solo_en_modo_personalizado(
        self,
        obtener_configuracion,
        obtener_subida_activa,
        obtener_tarifas_personalizadas,
    ):
        tramos = [{"minuto_inicio": 0, "minuto_fin": 59, "valor": 800}]
        obtener_configuracion.return_value = {"modo_cobro": "personalizado"}
        obtener_subida_activa.return_value = None
        obtener_tarifas_personalizadas.return_value = tramos

        contexto = obtener_contexto_tarifa()

        self.assertEqual(contexto["tramos"], tramos)
        obtener_configuracion.assert_called_once()
        obtener_subida_activa.assert_called_once()
        obtener_tarifas_personalizadas.assert_called_once()

    def test_calcular_tarifa_con_contexto_mantiene_modo_minuto(self):
        contexto = {
            "config": {
                "modo_cobro": "minuto",
                "tarifa_minima": "300",
                "valor_minuto": "25",
            },
            "subida": None,
            "tramos": [],
        }

        tarifa = calcular_tarifa_con_contexto(10, contexto=contexto)

        self.assertEqual(tarifa, 525)

    def test_calcular_tarifa_con_contexto_usa_tramos_precargados(self):
        contexto = {
            "config": {"modo_cobro": "personalizado", "tarifa_minima": "300"},
            "subida": None,
            "tramos": [
                {"minuto_inicio": 0, "minuto_fin": 29, "valor": 500},
                {"minuto_inicio": 30, "minuto_fin": 59, "valor": 900},
            ],
        }

        tarifa = calcular_tarifa_con_contexto(45, contexto=contexto)

        self.assertEqual(tarifa, 900)

    @patch.object(tarifas_controller, "obtener_contexto_tarifa")
    @patch.object(tarifas_controller, "calcular_tarifa_con_contexto")
    def test_calcular_tarifa_sigue_usando_api_publica_existente(
        self,
        calcular_tarifa_con_contexto_mock,
        obtener_contexto_tarifa_mock,
    ):
        contexto = {"config": {"modo_cobro": "minuto"}, "subida": None, "tramos": []}
        obtener_contexto_tarifa_mock.return_value = contexto
        calcular_tarifa_con_contexto_mock.return_value = 1000
        ingreso = datetime(2026, 1, 1, 10, 0)
        salida = datetime(2026, 1, 1, 10, 30)

        tarifa = calcular_tarifa(30, ingreso, salida, devolver_flag=True)

        self.assertEqual(tarifa, 1000)
        calcular_tarifa_con_contexto_mock.assert_called_once_with(
            30,
            fecha_hora_ingreso=ingreso,
            fecha_hora_salida=salida,
            contexto=contexto,
            devolver_flag=True,
        )


if __name__ == "__main__":
    unittest.main()
