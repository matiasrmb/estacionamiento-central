import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from controllers import registro_controller


class FakeCursor:
    def __init__(self, fetchone_results=None, fetchall_results=None):
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])
        self.executed = []
        self.closed = False
        self.lastrowid = 123
        self.rowcount = 1

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

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor
        self.committed = False
        self.closed = False

    def cursor(self, *args, **kwargs):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


class FakeDbCursorContext:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, traceback):
        return False


class RegistrarIngresoTests(unittest.TestCase):
    @patch.object(registro_controller, "generar_ticket_ingreso")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_registra_ingreso_si_la_patente_ya_tiene_un_ingreso_activo(
        self,
        db_cursor,
        obtener_activos,
        generar_ticket,
    ):
        obtener_activos.return_value = [{"id_ingreso": 1, "patente": "ABC123"}]

        resultado = registro_controller.registrar_ingreso("ABC123")

        self.assertFalse(resultado)
        db_cursor.assert_not_called()
        generar_ticket.assert_not_called()

    @patch.object(registro_controller, "generar_ticket_ingreso")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registra_ingreso_creando_vehiculo_si_no_existe(
        self,
        db_cursor,
        obtener_activos,
        generar_ticket,
    ):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []

        resultado = registro_controller.registrar_ingreso("ABC123")

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(commit=True)
        generar_ticket.assert_called_once()
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO vehiculos", consultas)
        self.assertIn("INSERT INTO ingresos", consultas)

    @patch.object(registro_controller, "generar_ticket_ingreso")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registra_ingreso_usando_vehiculo_existente(
        self,
        db_cursor,
        obtener_activos,
        generar_ticket,
    ):
        cursor = FakeCursor(fetchone_results=[(77,)])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []

        resultado = registro_controller.registrar_ingreso("ABC123")

        self.assertTrue(resultado)
        generar_ticket.assert_called_once()
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("SELECT id_vehiculo", consultas)
        self.assertNotIn("INSERT INTO vehiculos", consultas)
        self.assertIn("INSERT INTO ingresos", consultas)


class CalcularMinutosEstadiaTests(unittest.TestCase):
    def test_calcula_minutos_entre_ingreso_y_salida(self):
        ingreso = datetime(2026, 1, 1, 10, 0, 0)
        salida = datetime(2026, 1, 1, 10, 45, 30)

        minutos = registro_controller.calcular_minutos_estadia(ingreso, salida)

        self.assertEqual(minutos, 45)

    def test_retorna_cero_si_la_salida_es_anterior_al_ingreso(self):
        ingreso = datetime(2026, 1, 1, 10, 0, 0)
        salida = datetime(2026, 1, 1, 9, 50, 0)

        minutos = registro_controller.calcular_minutos_estadia(ingreso, salida)

        self.assertEqual(minutos, 0)


class ObtenerIngresoActivoPriorizadoTests(unittest.TestCase):
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    def test_retorna_none_si_no_hay_ingresos_activos(self, obtener_activos):
        obtener_activos.return_value = []

        ingreso = registro_controller.obtener_ingreso_activo_priorizado("ABC123")

        self.assertIsNone(ingreso)

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    def test_retorna_el_primer_ingreso_activo_priorizado(self, obtener_activos):
        ingreso_priorizado = {"id_ingreso": 1, "en_espera": 0}
        obtener_activos.return_value = [
            ingreso_priorizado,
            {"id_ingreso": 2, "en_espera": 1},
        ]

        ingreso = registro_controller.obtener_ingreso_activo_priorizado("ABC123")

        self.assertEqual(ingreso, ingreso_priorizado)


class BuscarEstadoVehiculoTests(unittest.TestCase):
    @patch.object(registro_controller, "db_cursor")
    def test_retorna_no_registrado_si_no_existe_vehiculo(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        estado = registro_controller.buscar_estado_vehiculo("ABC123")

        self.assertEqual(estado, "no_registrado")
        db_cursor.assert_called_once_with(dictionary=True)

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_retorna_dentro_si_existen_ingresos_activos(self, db_cursor, obtener_activos):
        cursor = FakeCursor(fetchone_results=[{"id_vehiculo": 1}])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = [{"id_ingreso": 10}]

        estado = registro_controller.buscar_estado_vehiculo("ABC123")

        self.assertEqual(estado, "dentro")

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_retorna_fuera_si_existe_vehiculo_sin_ingresos_activos(self, db_cursor, obtener_activos):
        cursor = FakeCursor(fetchone_results=[{"id_vehiculo": 1}])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []

        estado = registro_controller.buscar_estado_vehiculo("ABC123")

        self.assertEqual(estado, "fuera")


class RegistrarSalidaTests(unittest.TestCase):
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_retorna_none_si_no_hay_ingresos_activos(self, db_cursor, obtener_activos):
        obtener_activos.return_value = []

        resultado = registro_controller.registrar_salida("ABC123", "admin")

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()

    @patch.object(registro_controller, "generar_ticket_salida")
    @patch.object(registro_controller, "obtener_configuracion")
    @patch.object(registro_controller, "calcular_tarifa")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registra_salida_calcula_tarifa_y_genera_ticket(
        self,
        db_cursor,
        obtener_activos,
        calcular_tarifa,
        obtener_configuracion,
        generar_ticket,
    ):
        cursor = FakeCursor()
        db_cursor.return_value = FakeDbCursorContext(cursor)
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        obtener_activos.return_value = [
            {
                "id_ingreso": 10,
                "fecha_hora_ingreso": fecha_ingreso,
                "patente": "ABC123",
            }
        ]
        calcular_tarifa.return_value = (1500, False, 0)
        obtener_configuracion.return_value = {"modo_cobro": "minuto"}

        resultado = registro_controller.registrar_salida("ABC123", "admin")

        self.assertEqual(resultado, 1500)
        db_cursor.assert_called_once_with(commit=True)
        calcular_tarifa.assert_called_once()
        generar_ticket.assert_called_once()
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE ingresos", consultas)

    @patch.object(registro_controller, "generar_ticket_salida")
    @patch.object(registro_controller, "obtener_configuracion")
    @patch.object(registro_controller, "calcular_tarifa")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_actualiza_salida_si_falla_obtener_configuracion(
        self,
        db_cursor,
        obtener_activos,
        calcular_tarifa,
        obtener_configuracion,
        generar_ticket,
    ):
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        obtener_activos.return_value = [
            {
                "id_ingreso": 10,
                "fecha_hora_ingreso": fecha_ingreso,
                "patente": "ABC123",
            }
        ]
        calcular_tarifa.return_value = (1500, False, 0)
        obtener_configuracion.side_effect = RuntimeError("config no disponible")

        resultado = registro_controller.registrar_salida("ABC123", "admin")

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()
        generar_ticket.assert_not_called()


class FuncionesSimplesDbCursorTests(unittest.TestCase):
    @patch.object(registro_controller, "revertir_en_espera")
    @patch.object(registro_controller, "marcar_ingreso_en_espera")
    @patch.object(registro_controller, "db_cursor")
    def test_alternar_estado_espera_revierte_si_existe_ingreso_en_espera(
        self,
        db_cursor,
        marcar_en_espera,
        revertir_en_espera,
    ):
        cursor = FakeCursor(fetchone_results=[{"id_ingreso": 10}])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        revertir_en_espera.return_value = True

        exito, mensaje = registro_controller.alternar_estado_espera("ABC123")

        self.assertTrue(exito)
        self.assertEqual(mensaje, "Revertido de estado 'en espera'.")
        db_cursor.assert_called_once_with(dictionary=True)
        revertir_en_espera.assert_called_once_with(10)
        marcar_en_espera.assert_not_called()

    @patch.object(registro_controller, "revertir_en_espera")
    @patch.object(registro_controller, "marcar_ingreso_en_espera")
    @patch.object(registro_controller, "db_cursor")
    def test_alternar_estado_espera_marca_si_no_existe_ingreso_en_espera(
        self,
        db_cursor,
        marcar_en_espera,
        revertir_en_espera,
    ):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        marcar_en_espera.return_value = True

        exito, mensaje = registro_controller.alternar_estado_espera("ABC123")

        self.assertTrue(exito)
        self.assertEqual(mensaje, "Marcado como 'en espera'.")
        marcar_en_espera.assert_called_once_with("ABC123")
        revertir_en_espera.assert_not_called()

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_retorna_false_si_no_existe_ingreso(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10)

        self.assertFalse(resultado)
        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO ingresos", consultas)
        self.assertNotIn("UPDATE ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_retorna_false_si_ya_tiene_activo(self, db_cursor):
        ingreso = {
            "id_vehiculo": 7,
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "tarifa_aplicada": 1500,
        }
        cursor = FakeCursor(fetchone_results=[ingreso, {"total": 1}])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10)

        self.assertFalse(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO ingresos", consultas)
        self.assertNotIn("UPDATE ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_inserta_nuevo_ingreso_y_marca_original(self, db_cursor):
        ingreso = {
            "id_vehiculo": 7,
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "tarifa_aplicada": 1500,
        }
        cursor = FakeCursor(fetchone_results=[ingreso, {"total": 0}])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10)

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO ingresos", consultas)
        self.assertIn("SET reingresado = 1", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_obtener_ingresos_editables_combina_en_espera_y_cerrados(self, db_cursor):
        en_espera = [{"id_ingreso": 1, "patente": "ABC123", "estado": "EN ESPERA"}]
        cerrados = [{"id_ingreso": 2, "patente": "XYZ789", "estado": "CERRADO"}]
        cursor = FakeCursor(fetchall_results=[en_espera, cerrados])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.obtener_ingresos_editables()

        self.assertEqual(resultado, en_espera + cerrados)
        db_cursor.assert_called_once_with(dictionary=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("'EN ESPERA' AS estado", consultas)
        self.assertIn("'CERRADO' AS estado", consultas)

    @patch.object(registro_controller, "obtener_contexto_tarifa")
    @patch.object(registro_controller, "calcular_tarifa_con_contexto")
    @patch.object(registro_controller, "db_cursor")
    def test_obtener_vehiculos_activos_formatea_activos_y_calcula_montos(
        self,
        db_cursor,
        calcular_tarifa_con_contexto,
        obtener_contexto_tarifa,
    ):
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        filas = [
            {
                "id_ingreso": 1,
                "patente": "ABC123",
                "fecha_hora_ingreso": fecha_ingreso,
                "en_espera": 0,
            },
            {
                "id_ingreso": 2,
                "patente": "XYZ789",
                "fecha_hora_ingreso": fecha_ingreso,
                "en_espera": 1,
            },
        ]
        cursor = FakeCursor(fetchall_results=[filas])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        contexto = {"config": {"modo_cobro": "minuto"}, "subida": None, "tramos": []}
        obtener_contexto_tarifa.return_value = contexto
        calcular_tarifa_con_contexto.return_value = 1200

        resultado = registro_controller.obtener_vehiculos_activos()

        db_cursor.assert_called_once_with(dictionary=True)
        obtener_contexto_tarifa.assert_called_once()
        calcular_tarifa_con_contexto.assert_called_once()
        self.assertIs(calcular_tarifa_con_contexto.call_args.args[3], contexto)
        self.assertEqual(resultado[0]["patente"], "ABC123")
        self.assertEqual(resultado[0]["monto"], 1200)
        self.assertEqual(resultado[1]["patente"], "XYZ789 [EN ESPERA]")
        self.assertEqual(resultado[1]["monto"], 0)
        self.assertTrue(resultado[1]["en_espera"])

    @patch.object(registro_controller, "obtener_contexto_tarifa")
    @patch.object(registro_controller, "calcular_tarifa_con_contexto")
    @patch.object(registro_controller, "db_cursor")
    def test_obtener_vehiculos_activos_reutiliza_contexto_tarifa_para_multiples_vehiculos(
        self,
        db_cursor,
        calcular_tarifa_con_contexto,
        obtener_contexto_tarifa,
    ):
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        filas = [
            {
                "id_ingreso": index,
                "patente": f"ABC{index}",
                "fecha_hora_ingreso": fecha_ingreso,
                "en_espera": 0,
            }
            for index in range(1, 6)
        ]
        cursor = FakeCursor(fetchall_results=[filas])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        contexto = {"config": {"modo_cobro": "minuto"}, "subida": None, "tramos": []}
        obtener_contexto_tarifa.return_value = contexto
        calcular_tarifa_con_contexto.return_value = 1200

        resultado = registro_controller.obtener_vehiculos_activos()

        self.assertEqual(len(resultado), 5)
        obtener_contexto_tarifa.assert_called_once()
        self.assertEqual(calcular_tarifa_con_contexto.call_count, 5)
        for call in calcular_tarifa_con_contexto.call_args_list:
            self.assertIs(call.args[3], contexto)

    @patch.object(registro_controller, "db_cursor")
    def test_obtener_ingresos_activos_por_patente_retorna_filas(self, db_cursor):
        ingresos = [
            {"id_ingreso": 1, "patente": "ABC123", "en_espera": 0},
            {"id_ingreso": 2, "patente": "ABC123", "en_espera": 1},
        ]
        cursor = FakeCursor(fetchall_results=[ingresos])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.obtener_ingresos_activos_por_patente("ABC123")

        self.assertEqual(resultado, ingresos)
        db_cursor.assert_called_once_with(dictionary=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM ingresos i", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_marcar_ingreso_en_espera_actualiza_ingreso_activo_normal(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[{"id_ingreso": 10}])
        cursor.rowcount = 1
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.marcar_ingreso_en_espera("ABC123")

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("SELECT i.id_ingreso", consultas)
        self.assertIn("UPDATE ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_marcar_ingreso_en_espera_retorna_false_si_no_hay_ingreso_normal(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.marcar_ingreso_en_espera("ABC123")

        self.assertFalse(resultado)

    @patch.object(registro_controller, "db_cursor")
    def test_eliminar_ingreso_con_respaldo_inserta_respaldo_y_elimina(self, db_cursor):
        ingreso = {
            "id_ingreso": 10,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
        }
        cursor = FakeCursor(fetchone_results=[ingreso])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO ingresos_eliminados", consultas)
        self.assertIn("DELETE FROM ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_eliminar_ingreso_con_respaldo_no_elimina_si_no_existe_ingreso(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO ingresos_eliminados", consultas)
        self.assertNotIn("DELETE FROM ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_registrar_uso_bano_inserta_registro(self, db_cursor):
        cursor = FakeCursor()
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.registrar_uso_bano(300, "admin")

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO usos_bano", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_revertir_en_espera_retorna_true_si_actualiza_fila(self, db_cursor):
        cursor = FakeCursor()
        cursor.rowcount = 1
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.revertir_en_espera(10)

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_revertir_en_espera_retorna_false_si_no_actualiza_fila(self, db_cursor):
        cursor = FakeCursor()
        cursor.rowcount = 0
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.revertir_en_espera(10)

        self.assertFalse(resultado)


if __name__ == "__main__":
    unittest.main()
