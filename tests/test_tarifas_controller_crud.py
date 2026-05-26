import unittest
from contextlib import contextmanager
from unittest.mock import patch

from controllers import tarifas_controller


class FakeCursor:
    def __init__(self, fetchall_results=None):
        self.fetchall_results = list(fetchall_results or [])
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class TarifasControllerCrudTests(unittest.TestCase):
    @patch.object(tarifas_controller, "db_cursor")
    def test_obtener_tarifas_personalizadas_retorna_tramos_ordenados(self, db_cursor):
        tramos = [{"id_tarifa": 1, "minuto_inicio": 0, "minuto_fin": 15, "valor": 300}]
        cursor = FakeCursor(fetchall_results=[tramos])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = tarifas_controller.obtener_tarifas_personalizadas()

        self.assertEqual(resultado, tramos)
        db_cursor.assert_called_once_with(dictionary=True)
        self.assertIn("ORDER BY minuto_inicio ASC", cursor.executed[0][0])

    @patch.object(tarifas_controller, "validar_intervalo")
    @patch.object(tarifas_controller, "db_cursor")
    def test_agregar_intervalo_inserta_si_no_hay_superposicion(self, db_cursor, validar_intervalo):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)
        validar_intervalo.return_value = True

        tarifas_controller.agregar_intervalo(0, 15, 300)

        db_cursor.assert_called_once_with(commit=True)
        self.assertIn("INSERT INTO tarifas_personalizadas", cursor.executed[0][0])

    @patch.object(tarifas_controller, "validar_intervalo")
    @patch.object(tarifas_controller, "db_cursor")
    def test_agregar_intervalo_rechaza_superposicion(self, db_cursor, validar_intervalo):
        validar_intervalo.return_value = False

        with self.assertRaises(ValueError):
            tarifas_controller.agregar_intervalo(0, 15, 300)

        db_cursor.assert_not_called()

    @patch.object(tarifas_controller, "validar_intervalo")
    @patch.object(tarifas_controller, "db_cursor")
    def test_actualizar_intervalo_actualiza_si_es_valido(self, db_cursor, validar_intervalo):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)
        validar_intervalo.return_value = True

        tarifas_controller.actualizar_intervalo(1, 0, 15, 300)

        db_cursor.assert_called_once_with(commit=True)
        self.assertIn("UPDATE tarifas_personalizadas", cursor.executed[0][0])

    @patch.object(tarifas_controller, "db_cursor")
    def test_eliminar_intervalo_elimina_por_id(self, db_cursor):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)

        tarifas_controller.eliminar_intervalo(1)

        db_cursor.assert_called_once_with(commit=True)
        self.assertIn("DELETE FROM tarifas_personalizadas", cursor.executed[0][0])

    @patch.object(tarifas_controller, "obtener_configuracion")
    @patch.object(tarifas_controller, "db_cursor")
    def test_generar_tramos_automaticos_reemplaza_tramos(self, db_cursor, obtener_configuracion):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)
        obtener_configuracion.return_value = {
            "tarifa_minima": "300",
            "tarifa_hora": "500",
        }

        resultado = tarifas_controller.generar_tramos_automaticos()

        self.assertTrue(resultado["ok"])
        self.assertEqual(resultado["tramos_generados"], 3)
        db_cursor.assert_called_once_with(commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("DELETE FROM tarifas_personalizadas", consultas)
        self.assertEqual(consultas.count("INSERT INTO tarifas_personalizadas"), 3)

    @patch.object(tarifas_controller, "db_cursor")
    def test_validar_intervalo_retorna_false_si_se_superpone(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[{"minuto_inicio": 10, "minuto_fin": 20}]])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = tarifas_controller.validar_intervalo(15, 25)

        self.assertFalse(resultado)
        db_cursor.assert_called_once_with(dictionary=True)

    @patch.object(tarifas_controller, "db_cursor")
    def test_validar_intervalo_retorna_true_si_no_se_superpone(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[{"minuto_inicio": 10, "minuto_fin": 20}]])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = tarifas_controller.validar_intervalo(21, 30)

        self.assertTrue(resultado)

    @patch.object(tarifas_controller, "db_cursor")
    def test_validar_intervalo_excluye_id_en_edicion(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[]])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = tarifas_controller.validar_intervalo(10, 20, id_excluir=5)

        self.assertTrue(resultado)
        query, params = cursor.executed[0]
        self.assertIn("WHERE id_tarifa != %s", query)
        self.assertEqual(params, (5,))


if __name__ == "__main__":
    unittest.main()
