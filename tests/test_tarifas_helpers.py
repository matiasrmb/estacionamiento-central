import unittest

from controllers.tarifas_controller import (
    construir_intervalos_equitativos,
    construir_valores_automaticos,
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


if __name__ == "__main__":
    unittest.main()
