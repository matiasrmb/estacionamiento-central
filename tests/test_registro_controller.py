import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from controllers import registro_controller
from utils import db as db_utils
from utils.print_jobs import (
    crear_print_job_ingreso,
    crear_print_job_salida,
    ingreso_idempotency_key,
    salida_idempotency_key,
)


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
        self.rolled_back = False
        self.executed_before_rollback = None
        self.closed = False

    def cursor(self, *args, **kwargs):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.executed_before_rollback = list(self.cursor_instance.executed)
        self.rolled_back = True

    def close(self):
        self.closed = True


class FakeDbCursorContext:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, traceback):
        return False


class FailingPrintJobCursor(FakeCursor):
    def execute(self, query, params=None):
        super().execute(query, params)
        if "INSERT INTO print_jobs" in query:
            raise RuntimeError("print job unavailable")


class UniqueSalidaPrintJobCursor(FakeCursor):
    def __init__(self, existing_key):
        super().__init__(fetchall_results=[[(existing_key,)]])
        self.existing_key = existing_key

    def execute(self, query, params=None):
        super().execute(query, params)
        if "INSERT INTO print_jobs" in query and params[-1] == self.existing_key:
            raise RuntimeError("Duplicate entry for key 'print_jobs.uq_idempotency'")


class FailingConfigLookupCursor(FakeCursor):
    def execute(self, query, params=None):
        if "FROM configuracion" in query:
            super().execute(query, params)
            raise RuntimeError("config no disponible")
        super().execute(query, params)


class FailingPrintJobUnlinkCursor(FakeCursor):
    def execute(self, query, params=None):
        super().execute(query, params)
        if "SET id_ingreso = NULL" in query:
            raise RuntimeError("print_jobs.id_ingreso cannot be null")


class FailingSalidaReversalAuditCursor(FakeCursor):
    def execute(self, query, params=None):
        super().execute(query, params)
        if "INSERT INTO reversiones_salida" in query:
            raise RuntimeError("reversion audit unavailable")


class VehicleLockResultCursor(FakeCursor):
    """Fails like mysql-connector if the vehicle lock result is not consumed."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vehicle_lock_result_pending = False

    def execute(self, query, params=None):
        if self.vehicle_lock_result_pending:
            raise RuntimeError("Unread result found")
        super().execute(query, params)
        if "FROM vehiculos" in query and "WHERE id_vehiculo = %s" in query:
            self.vehicle_lock_result_pending = True

    def fetchone(self):
        result = super().fetchone()
        self.vehicle_lock_result_pending = False
        return result


class RegistrarIngresoTests(unittest.TestCase):
    def test_obtener_opcion_noches_requiere_configuracion_activa_y_valida(self):
        configuracion = {
            "noches_activo": "1",
            "noches_hora_inicio": "22:00",
            "noches_hora_fin": "08:00",
            "noches_valor": "5000",
        }
        opcion = registro_controller.obtener_opcion_noches(configuracion, datetime(2026, 1, 1, 23, 0))

        self.assertEqual(opcion, {
            "monto_snapshot": 5000,
            "hora_inicio_snapshot": "19:30",
            "hora_fin_snapshot": "09:30",
        })
        self.assertIsNone(registro_controller.obtener_opcion_noches({"noches_activo": "0"}, datetime(2026, 1, 1, 23, 0)))

    def test_obtener_opcion_noches_usa_referencia_fija_e_ignora_horarios_heredados(self):
        configuracion = {
            "noches_activo": "1",
            "noches_hora_inicio": "09:00",
            "noches_hora_fin": "17:00",
            "noches_valor": "5000",
        }

        opcion = registro_controller.obtener_opcion_noches(configuracion, datetime(2026, 1, 1, 12, 0))

        self.assertEqual(opcion["hora_inicio_snapshot"], "19:30")
        self.assertEqual(opcion["hora_fin_snapshot"], "09:30")

    def test_obtener_opcion_noches_rechaza_inactiva_o_sin_valor(self):
        configuracion = {
            "noches_activo": "1",
            "noches_hora_inicio": "20:00",
            "noches_hora_fin": "08:00",
            "noches_valor": "5000",
        }

        self.assertIsNone(registro_controller.obtener_opcion_noches({**configuracion, "noches_activo": "0"}, datetime(2026, 1, 1, 21, 0)))
        self.assertIsNone(registro_controller.obtener_opcion_noches({**configuracion, "noches_valor": "0"}, datetime(2026, 1, 1, 21, 0)))

    @patch.object(registro_controller, "obtener_configuracion")
    @patch.object(registro_controller, "db_cursor")
    def test_registra_ingreso_y_cobro_noches_en_la_misma_operacion(self, db_cursor, obtener_configuracion):
        cursor = FakeCursor(fetchone_results=[(77,)])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_configuracion.return_value = {
            "noches_activo": "1",
            "noches_hora_inicio": "00:00",
            "noches_hora_fin": "23:59",
            "noches_valor": "5000",
        }

        resultado = registro_controller.registrar_ingreso_con_noches_detallado("ABC123", "operador")

        self.assertEqual(resultado["cobro_noche"]["monto_snapshot"], 5000)
        cobro_params = next(
            params for query, params in cursor.executed if "INSERT INTO cobros_noches" in query
        )
        self.assertEqual(cobro_params[:4], (123, 5000, "19:30", "09:30"))
        self.assertEqual(cobro_params[-1], "operador")
        print_job = next(params for query, params in cursor.executed if "INSERT INTO print_jobs" in query)
        self.assertEqual(json.loads(print_job[4])["noches"]["monto_snapshot"], 5000)

    @patch.object(registro_controller, "db_cursor")
    def test_no_registra_ingreso_si_la_patente_ya_tiene_un_ingreso_activo(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[(77,), {"id_ingreso": 1}])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.registrar_ingreso("ABC123")

        self.assertFalse(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM vehiculos WHERE patente = %s FOR UPDATE", consultas)
        self.assertIn("fecha_hora_salida IS NULL", consultas)
        self.assertIn("FOR UPDATE", consultas)
        self.assertNotIn("INSERT INTO ingresos", consultas)

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registra_ingreso_creando_vehiculo_si_no_existe(
        self,
        db_cursor,
        obtener_activos,
    ):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []

        resultado = registro_controller.registrar_ingreso_detallado("ABC123")

        self.assertIsNotNone(resultado)
        db_cursor.assert_any_call(commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO vehiculos", consultas)
        self.assertIn("INSERT INTO ingresos", consultas)
        self.assertIn("INSERT INTO print_jobs", consultas)

        print_job = next(
            params for query, params in cursor.executed
            if "INSERT INTO print_jobs" in query
        )
        self.assertEqual(print_job[1], "PC_PDF")
        self.assertEqual(print_job[2], 123)
        self.assertEqual(print_job[3], "ABC123")
        self.assertEqual(print_job[5], "PENDIENTE")
        self.assertEqual(print_job[6], "desktop-ingreso:123:pc-pdf")
        self.assertEqual(print_job[4], json.dumps({
            "kind": "TICKET_INGRESO",
            "id_ingreso": 123,
            "patente": "ABC123",
            "hora_ingreso": resultado["fecha_hora_ingreso"].isoformat(timespec="seconds"),
            "usuario": {"id_usuario": None, "usuario": None, "rol": None},
            "tarifa": {"monto_preliminar": 0},
            "meta": {
                "server_time": resultado["fecha_hora_ingreso"].isoformat(timespec="seconds"),
                "version": 1,
            },
        }, ensure_ascii=False))

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "obtener_print_jobs_pc_activos", return_value=False)
    @patch.object(registro_controller, "db_cursor")
    def test_registra_ingreso_sin_crear_job_cuando_la_impresion_pc_esta_desactivada(
        self, db_cursor, _obtener_print_jobs_pc_activos, obtener_activos
    ):
        cursor = FakeCursor(fetchone_results=[(77,)])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []

        resultado = registro_controller.registrar_ingreso_detallado("ABC123")

        self.assertIsNotNone(resultado)
        self.assertIn("INSERT INTO ingresos", "\n".join(query for query, _ in cursor.executed))
        self.assertNotIn("INSERT INTO print_jobs", "\n".join(query for query, _ in cursor.executed))

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registrar_ingreso_detallado_retorna_fecha_de_ingreso(
        self,
        db_cursor,
        obtener_activos,
    ):
        cursor = FakeCursor(fetchone_results=[(77,)])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []

        resultado = registro_controller.registrar_ingreso_detallado("ABC123")

        self.assertEqual(resultado["patente"], "ABC123")
        self.assertIsInstance(resultado["fecha_hora_ingreso"], datetime)

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registra_ingreso_usando_vehiculo_existente(
        self,
        db_cursor,
        obtener_activos,
    ):
        cursor = FakeCursor(fetchone_results=[(77,)])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []

        resultado = registro_controller.registrar_ingreso("ABC123")

        self.assertTrue(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("SELECT id_vehiculo", consultas)
        self.assertNotIn("INSERT INTO vehiculos", consultas)
        self.assertIn("INSERT INTO ingresos", consultas)

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registrar_ingreso_detallado_usa_fecha_hora_personalizada_valida(
        self,
        db_cursor,
        obtener_activos,
    ):
        cursor = FakeCursor(fetchone_results=[(77,)])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []
        fecha_personalizada = datetime.now().replace(second=0, microsecond=0) - timedelta(hours=1)

        resultado = registro_controller.registrar_ingreso_detallado("ABC123", fecha_personalizada)

        self.assertEqual(resultado["fecha_hora_ingreso"], fecha_personalizada)
        insert_ingreso = next(
            params for query, params in cursor.executed
            if "INSERT INTO ingresos" in query
        )
        self.assertEqual(insert_ingreso, (77, fecha_personalizada))

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registrar_ingreso_retorna_true_con_fecha_hora_personalizada_valida(
        self,
        db_cursor,
        obtener_activos,
    ):
        cursor = FakeCursor(fetchone_results=[(77,)])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []
        fecha_personalizada = datetime.now().replace(second=0, microsecond=0) - timedelta(hours=2)

        resultado = registro_controller.registrar_ingreso("ABC123", fecha_personalizada)

        self.assertTrue(resultado)

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    def test_registrar_ingreso_hace_rollback_si_falla_el_job_durable(self, obtener_activos):
        cursor = FailingPrintJobCursor(fetchone_results=[(77,)])
        connection = FakeConnection(cursor)
        obtener_activos.return_value = []

        with patch.object(registro_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            resultado = registro_controller.registrar_ingreso("ABC123")

        self.assertFalse(resultado)
        self.assertFalse(connection.committed)
        self.assertTrue(connection.rolled_back)

        queries_before_rollback = [
            query for query, _ in connection.executed_before_rollback
        ]
        ingreso_index = next(
            index for index, query in enumerate(queries_before_rollback)
            if "INSERT INTO ingresos" in query
        )
        print_job_index = next(
            index for index, query in enumerate(queries_before_rollback)
            if "INSERT INTO print_jobs" in query
        )

        self.assertLess(ingreso_index, print_job_index)

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    def test_registrar_ingreso_confirma_y_crea_job_si_falla_la_lectura_de_configuracion(
        self, obtener_activos
    ):
        cursor = FailingConfigLookupCursor(fetchone_results=[(77,)])
        connection = FakeConnection(cursor)
        obtener_activos.return_value = []

        with patch.object(registro_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            resultado = registro_controller.registrar_ingreso("ABC123")

        self.assertTrue(resultado)
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO ingresos", consultas)
        self.assertIn("INSERT INTO print_jobs", consultas)

    def test_clave_idempotencia_de_ingreso_es_estable(self):
        self.assertEqual(ingreso_idempotency_key(123), "desktop-ingreso:123:pc-pdf")
        self.assertEqual(ingreso_idempotency_key(123), ingreso_idempotency_key(123))

    def test_helper_crea_un_job_durable_de_ingreso(self):
        cursor = FakeCursor()
        fecha = datetime(2026, 7, 24, 10, 30)

        crear_print_job_ingreso(cursor, 123, "ABC123", fecha)

        self.assertEqual(len(cursor.executed), 1)
        query, params = cursor.executed[0]
        self.assertIn("INSERT INTO print_jobs", query)
        self.assertEqual(params[:4], ("TICKET_INGRESO", "PC_PDF", 123, "ABC123"))
        self.assertEqual(params[5:], ("PENDIENTE", "desktop-ingreso:123:pc-pdf"))

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_registra_ingreso_personalizado_futuro(
        self,
        db_cursor,
        obtener_activos,
    ):
        obtener_activos.return_value = []
        fecha_futura = datetime.now() + timedelta(minutes=5)

        resultado = registro_controller.registrar_ingreso_detallado("ABC123", fecha_futura)

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_registra_ingreso_personalizado_mayor_a_cuatro_horas(
        self,
        db_cursor,
        obtener_activos,
    ):
        obtener_activos.return_value = []
        fecha_antigua = datetime.now() - timedelta(hours=4, minutes=1)

        resultado = registro_controller.registrar_ingreso_detallado("ABC123", fecha_antigua)

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_registra_ingreso_personalizado_de_dia_anterior(
        self,
        db_cursor,
        obtener_activos,
    ):
        obtener_activos.return_value = []
        fecha_anterior = datetime.now() - timedelta(days=1)

        resultado = registro_controller.registrar_ingreso_detallado("ABC123", fecha_anterior)

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()


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


class OrdenarPatentesTurnoParaF4Tests(unittest.TestCase):
    def setUp(self):
        self.filas = [
            {"id_ingreso": 3, "patente": "ZZZ999", "fecha_hora_ingreso": datetime(2026, 1, 1, 9, 0)},
            {"id_ingreso": 2, "patente": "AB-CD12", "fecha_hora_ingreso": datetime(2026, 1, 1, 11, 0)},
            {"id_ingreso": 1, "patente": "ABCD12", "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0)},
            {"id_ingreso": 4, "patente": "XXABCD12", "fecha_hora_ingreso": datetime(2026, 1, 1, 8, 0)},
        ]

    def test_orden_vacio_es_alfabetico(self):
        resultado = registro_controller.ordenar_patentes_turno_para_f4(self.filas, "  ")

        self.assertEqual([fila["patente"] for fila in resultado], ["AB-CD12", "ABCD12", "XXABCD12", "ZZZ999"])

    def test_prioriza_exacta_luego_prefijo_y_contiene(self):
        exacta = registro_controller.ordenar_patentes_turno_para_f4(self.filas, "ab cd12")
        prefijo = registro_controller.ordenar_patentes_turno_para_f4(self.filas, "abc")
        contiene = registro_controller.ordenar_patentes_turno_para_f4(self.filas, "xab")

        self.assertEqual([fila["id_ingreso"] for fila in exacta], [1, 2, 4])
        self.assertEqual([fila["id_ingreso"] for fila in prefijo], [1, 2, 4])
        self.assertEqual([fila["id_ingreso"] for fila in contiene], [4])

    def test_ordena_globalmente_por_distancia_antes_que_contiene(self):
        filas = [
            {"id_ingreso": 1, "patente": "XABC123Y", "fecha_hora_ingreso": datetime(2026, 1, 1, 8, 0)},
            {"id_ingreso": 2, "patente": "ABC124", "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0)},
        ]

        resultado = registro_controller.ordenar_patentes_turno_para_f4(filas, "ABC123")

        self.assertEqual([fila["id_ingreso"] for fila in resultado], [2, 1])

    def test_orden_de_coincidencias_usa_movimiento_mas_antiguo(self):
        filas = [
            {"id_ingreso": 3, "patente": "ABC123", "fecha_hora_ingreso": datetime(2026, 1, 1, 12, 0)},
            {"id_ingreso": 2, "patente": "ABC124", "fecha_hora_ingreso": datetime(2026, 1, 1, 9, 0)},
            {"id_ingreso": 1, "patente": "ABC125", "fecha_hora_ingreso": datetime(2026, 1, 1, 8, 0), "fecha_hora_salida": datetime(2026, 1, 1, 10, 0)},
        ]

        resultado = registro_controller.ordenar_patentes_turno_para_f4(filas, "ABC")

        self.assertEqual([fila["id_ingreso"] for fila in resultado], [2, 1, 3])

    def test_desempata_por_id_despues_del_movimiento(self):
        fecha = datetime(2026, 1, 1, 9, 0)
        filas = [
            {"id_ingreso": 2, "patente": "ABC123", "fecha_hora_ingreso": fecha},
            {"id_ingreso": 1, "patente": "ABC124", "fecha_hora_ingreso": fecha},
        ]

        resultado = registro_controller.ordenar_patentes_turno_para_f4(filas, "ABC")

        self.assertEqual([fila["id_ingreso"] for fila in resultado], [1, 2])


class OrdenarPatentesParaBusquedaTests(unittest.TestCase):
    def test_orden_vacio_es_alfabetico_para_f3(self):
        filas = [
            {"id_ingreso": 2, "patente": "ZZZ999", "hora": "2026-01-01 09:00:00"},
            {"id_ingreso": 1, "patente": "ABC123", "hora": "2026-01-01 10:00:00"},
        ]

        resultado = registro_controller.ordenar_patentes_para_busqueda(filas, "", campo_fecha="hora")

        self.assertEqual([fila["patente"] for fila in resultado], ["ABC123", "ZZZ999"])


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


class PreviewSalidaTests(unittest.TestCase):
    @patch.object(registro_controller, "obtener_ingreso_activo_priorizado")
    @patch.object(registro_controller, "calcular_tarifa")
    def test_preview_noche_pendiente_no_calcula_estacionamiento(self, calcular_tarifa, obtener_ingreso):
        obtener_ingreso.return_value = {
            "id_ingreso": 10,
            "patente": "XX0011",
            "en_espera": 0,
            "en_lavado": 0,
            "noches_prepagadas": [{"estado_operativo": "PENDIENTE", "monto_snapshot": 5000}],
        }

        resultado = registro_controller.obtener_preview_salida_por_patente("XX0011")

        self.assertEqual(resultado, {"estado": "noche_pendiente", "patente": "XX0011"})
        calcular_tarifa.assert_not_called()


class NochesPendientesTests(unittest.TestCase):
    @patch.object(registro_controller, "asegurar_schema_noches")
    @patch.object(registro_controller, "db_cursor")
    def test_busqueda_noche_pendiente_excluye_ingreso_anulado(self, db_cursor, _asegurar_schema):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.obtener_noche_pendiente_por_patente("ABC123")

        self.assertIsNone(resultado)
        consulta, params = cursor.executed[0]
        self.assertIn("FROM ingresos_eliminados", consulta)
        self.assertIn("ie.id_ingreso_original = i.id_ingreso", consulta)
        self.assertEqual(params, ("ABC123",))

    @patch.object(registro_controller, "asegurar_schema_noches")
    @patch.object(registro_controller, "db_cursor")
    def test_busqueda_noche_pendiente_normal_se_mantiene_disponible(self, db_cursor, _asegurar_schema):
        pendiente = {"id_ingreso": 10, "patente": "ABC123", "fecha_hora_pago": datetime(2026, 7, 30, 20, 0)}
        cursor = FakeCursor(fetchone_results=[pendiente])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.obtener_noche_pendiente_por_patente("ABC123")

        self.assertEqual(resultado, pendiente)

    @patch.object(registro_controller, "asegurar_schema_noches")
    @patch.object(registro_controller, "db_cursor")
    def test_finalizar_noche_pendiente_cierra_sin_cobro_adicional(self, db_cursor, _asegurar_schema):
        cursor = FakeCursor(fetchone_results=[{"id_cobro_noche": 7}])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.finalizar_noche_pendiente(10, "operador")

        self.assertTrue(resultado)
        estado_noche = next(
            params for query, params in cursor.executed if "estado_operativo = 'RETIRADO'" in query
        )
        salida = next(
            params for query, params in cursor.executed if "tarifa_aplicada = 0" in query
        )
        self.assertIsInstance(estado_noche[0], datetime)
        self.assertEqual(estado_noche[1], 7)
        self.assertEqual(salida[0], estado_noche[0])
        self.assertEqual(salida[1:], ("operador", 10))

    @patch.object(registro_controller, "asegurar_schema_noches")
    @patch.object(registro_controller, "db_cursor")
    def test_no_finaliza_noche_pendiente_de_ingreso_anulado(self, db_cursor, _asegurar_schema):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.finalizar_noche_pendiente(10, "operador")

        self.assertFalse(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM ingresos_eliminados", consultas)
        self.assertNotIn("estado_operativo = 'RETIRADO'", consultas)
        self.assertNotIn("tarifa_aplicada = 0", consultas)

    @patch.object(registro_controller, "asegurar_schema_noches")
    @patch.object(registro_controller, "db_cursor")
    @patch.object(registro_controller, "datetime", wraps=datetime)
    def test_convertir_noche_a_ingreso_normal_ancla_en_el_fin_de_la_noche_pagada(
        self, mocked_datetime, db_cursor, _asegurar_schema
    ):
        for pago, resolucion, esperado in (
            (datetime(2026, 7, 30, 9, 30), datetime(2026, 7, 31, 12, 0), datetime(2026, 7, 30, 10, 0)),
            (datetime(2026, 7, 30, 16, 0), datetime(2026, 7, 31, 12, 0), datetime(2026, 7, 31, 10, 0)),
        ):
            with self.subTest(pago=pago):
                cursor = FakeCursor(fetchone_results=[{
                    "id_cobro_noche": 7,
                    "fecha_hora_pago": pago,
                }])
                db_cursor.return_value = FakeDbCursorContext(cursor)
                mocked_datetime.now.return_value = resolucion

                inicio = registro_controller.convertir_noche_a_ingreso_normal(10, "operador")

                self.assertEqual(inicio, esperado)
                estado_noche = next(
                    params for query, params in cursor.executed if "estado_operativo = 'CONVERTIDO'" in query
                )
                ingreso = next(
                    params for query, params in cursor.executed if "SET fecha_hora_ingreso" in query
                )
                self.assertEqual(estado_noche, (resolucion, 7))
                self.assertEqual(ingreso, (esperado, "operador", 10))

    @patch.object(registro_controller, "asegurar_schema_noches")
    @patch.object(registro_controller, "db_cursor")
    def test_no_convierte_noche_pendiente_de_ingreso_anulado(self, db_cursor, _asegurar_schema):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.convertir_noche_a_ingreso_normal(10, "operador")

        self.assertIsNone(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM ingresos_eliminados", consultas)
        self.assertNotIn("estado_operativo = 'CONVERTIDO'", consultas)
        self.assertNotIn("SET fecha_hora_ingreso", consultas)

    @patch.object(registro_controller, "obtener_operacion_convertida_por_ingreso", return_value=None)
    @patch.object(registro_controller, "calcular_total_lavados", return_value=0)
    @patch.object(registro_controller, "calcular_tarifa", return_value=(1500, False, 0))
    @patch.object(registro_controller, "calcular_minutos_lavado", return_value=0)
    def test_noche_convertida_cobra_salida_normal_desde_las_diez(
        self,
        _minutos_lavado,
        calcular_tarifa,
        _total_lavados,
        _operacion_convertida,
    ):
        inicio = datetime(2026, 7, 31, 10, 0)
        detalle = registro_controller._calcular_detalle_salida({
            "id_ingreso": 10,
            "fecha_hora_ingreso": inicio,
            "noches_prepagadas": [{"estado_operativo": "CONVERTIDO", "monto_snapshot": 5000}],
        }, datetime(2026, 7, 31, 11, 0))

        self.assertEqual(detalle["minutos"], 60)
        self.assertEqual(detalle["tarifa_estacionamiento"], 1500)
        calcular_tarifa.assert_called_once_with(
            60, inicio, datetime(2026, 7, 31, 11, 0), devolver_flag=True
        )

    @patch.object(registro_controller, "asegurar_schema_noches")
    @patch.object(registro_controller, "obtener_totales_lavado_por_ingresos", return_value={})
    @patch.object(registro_controller, "obtener_minutos_lavado_por_ingresos", return_value={})
    @patch.object(registro_controller, "obtener_contexto_tarifa")
    @patch.object(registro_controller, "calcular_tarifa_con_contexto")
    @patch.object(registro_controller, "db_cursor")
    def test_noche_pendiente_no_acumula_estacionamiento_en_activos(
        self,
        db_cursor,
        calcular_tarifa,
        _obtener_contexto,
        _minutos_lavado,
        _totales_lavado,
        _asegurar_schema,
    ):
        cursor = FakeCursor(fetchall_results=[[{
            "id_ingreso": 10,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 7, 30, 20, 0),
            "en_espera": 0,
            "en_lavado": 0,
            "modo_noche": 1,
        }]])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.obtener_vehiculos_activos()

        self.assertEqual(resultado[0]["minutos"], 0)
        self.assertEqual(resultado[0]["monto"], 0)
        self.assertTrue(resultado[0]["noche_pendiente"])
        calcular_tarifa.assert_not_called()

    def test_modo_noche_factura_solo_minutos_fuera_de_la_gracia(self):
        for ingreso, salida, esperado in (
            (datetime(2026, 7, 30, 19, 0), datetime(2026, 7, 31, 10, 0), {"antes": 0, "despues": 0, "total": 0}),
            (datetime(2026, 7, 30, 18, 40), datetime(2026, 7, 31, 9, 30), {"antes": 20, "despues": 0, "total": 20}),
            (datetime(2026, 7, 30, 19, 30), datetime(2026, 7, 31, 10, 20), {"antes": 0, "despues": 20, "total": 20}),
        ):
            with self.subTest(ingreso=ingreso, salida=salida):
                self.assertEqual(registro_controller.calcular_minutos_fuera_modo_noche(ingreso, salida), esperado)

    def test_lavado_que_cruza_inicio_de_gracia_descuenta_solo_el_solapamiento_cobrable(self):
        ingreso = datetime(2026, 7, 30, 18, 40)
        salida = datetime(2026, 7, 31, 9, 30)
        intervalos = registro_controller.descontar_intervalos(
            registro_controller.calcular_intervalos_fuera_modo_noche(ingreso, salida),
            [(datetime(2026, 7, 30, 18, 45), datetime(2026, 7, 30, 19, 15))],
        )

        self.assertEqual(intervalos, [(ingreso, datetime(2026, 7, 30, 18, 45))])
        self.assertEqual(sum(
            registro_controller.calcular_minutos_estadia(inicio, fin)
            for inicio, fin in intervalos
        ), 5)

    def test_salida_exacta_a_las_diez_no_tiene_extra_nocturno(self):
        ingreso = datetime(2026, 7, 30, 19, 30)
        salida = datetime(2026, 7, 31, 10, 0)

        self.assertEqual(
            registro_controller.calcular_intervalos_fuera_modo_noche(ingreso, salida), []
        )

    def test_lavado_que_cruza_fin_de_gracia_descuenta_solo_diez_minutos_cobrables(self):
        ingreso = datetime(2026, 7, 30, 19, 30)
        salida = datetime(2026, 7, 31, 10, 20)
        intervalos = registro_controller.descontar_intervalos(
            registro_controller.calcular_intervalos_fuera_modo_noche(ingreso, salida),
            [(datetime(2026, 7, 31, 9, 50), datetime(2026, 7, 31, 10, 10))],
        )

        self.assertEqual(intervalos, [(datetime(2026, 7, 31, 10, 10), salida)])
        self.assertEqual(sum(
            registro_controller.calcular_minutos_estadia(inicio, fin)
            for inicio, fin in intervalos
        ), 10)

    def test_recargo_en_gracia_no_se_aplica_y_recargo_en_extra_si(self):
        intervalo_extra = [(datetime(2026, 7, 31, 10, 0), datetime(2026, 7, 31, 10, 20))]
        contexto = {
            "config": {"modo_cobro": "minuto", "tarifa_minima": "0", "valor_minuto": "0"},
            "tramos": [],
        }

        contexto["subida"] = {
            "hora_inicio": "09:00:00", "hora_fin": "10:00:00", "monto_adicional": 100,
        }
        tarifa, subida, extra = registro_controller.calcular_tarifa_por_intervalos(
            intervalo_extra, contexto
        )
        self.assertEqual((tarifa, subida, extra), (0, False, 0))

        contexto["subida"] = {
            "hora_inicio": "10:00:00", "hora_fin": "10:10:00", "monto_adicional": 100,
        }
        tarifa, subida, extra = registro_controller.calcular_tarifa_por_intervalos(
            intervalo_extra, contexto
        )
        self.assertEqual((tarifa, subida, extra), (1000, True, 1000))

    @patch.object(registro_controller, "calcular_total_lavados", return_value=2500)
    @patch.object(registro_controller, "obtener_operacion_convertida_por_ingreso", return_value=None)
    @patch.object(registro_controller, "obtener_intervalos_lavado")
    @patch.object(registro_controller, "calcular_tarifa_por_intervalos", return_value=(1800, False, 0))
    @patch.object(registro_controller, "calcular_tarifa", return_value=(1800, False, 0))
    @patch.object(registro_controller, "calcular_minutos_lavado", return_value=10)
    @patch.object(registro_controller, "obtener_ingreso_activo_priorizado")
    def test_preview_activo_calcula_importes_sin_persistir(
        self,
        obtener_ingreso,
        calcular_minutos_lavado,
        calcular_tarifa,
        calcular_tarifa_por_intervalos,
        obtener_intervalos_lavado,
        obtener_operacion_convertida,
        calcular_total_lavados,
    ):
        fecha_ingreso = datetime(2026, 1, 1, 10, 0)
        fecha_consulta = datetime(2026, 1, 1, 11, 0)
        obtener_ingreso.return_value = {
            "id_ingreso": 10,
            "patente": "XX0011",
            "fecha_hora_ingreso": fecha_ingreso,
            "en_espera": 0,
            "en_lavado": 0,
            "noches_prepagadas": [{
                "monto_snapshot": 5000,
                "hora_inicio_snapshot": "22:00",
                "hora_fin_snapshot": "08:00",
            }],
        }
        obtener_intervalos_lavado.return_value = [(fecha_ingreso, fecha_ingreso + timedelta(minutes=10))]

        resultado = registro_controller.obtener_preview_salida_por_patente(
            "XX0011", fecha_consulta
        )

        self.assertEqual(resultado["estado"], "dentro")
        self.assertEqual(resultado["patente"], "XX0011")
        self.assertEqual(resultado["minutos"], 50)
        self.assertEqual(resultado["tarifa_estacionamiento"], 1800)
        self.assertEqual(resultado["total_lavados"], 2500)
        self.assertEqual(resultado["tarifa"], 4300)
        self.assertEqual(resultado["total_noches_prepagadas"], 5000)
        self.assertEqual(resultado["tarifa"], 4300)
        calcular_tarifa.assert_called_once()
        calcular_tarifa_por_intervalos.assert_not_called()

    @patch.object(registro_controller, "calcular_tarifa")
    @patch.object(registro_controller, "obtener_ingreso_activo_priorizado")
    def test_preview_no_calcula_para_ingreso_en_espera(self, obtener_ingreso, calcular_tarifa):
        obtener_ingreso.return_value = {"en_espera": 1, "en_lavado": 0}

        resultado = registro_controller.obtener_preview_salida_por_patente("XX0011")

        self.assertEqual(resultado, {"estado": "en_espera"})
        calcular_tarifa.assert_not_called()


class RegistrarSalidaTests(unittest.TestCase):
    @patch.object(registro_controller, "obtener_configuracion", return_value={"modo_cobro": "minuto"})
    @patch.object(registro_controller, "calcular_tarifa_por_intervalos", return_value=(1500, False, 0))
    @patch.object(registro_controller, "calcular_tarifa", return_value=(1500, False, 0))
    @patch.object(registro_controller, "calcular_minutos_lavado", return_value=0)
    @patch.object(registro_controller, "obtener_operacion_convertida_por_ingreso", return_value=None)
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_salida_informa_noches_prepagadas_sin_sumarlas_a_tarifa_aplicada(
        self, db_cursor, obtener_ingresos, _operacion, _minutos, _tarifa, _tarifa_intervalos, _configuracion
    ):
        cursor = FakeCursor()
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_ingresos.return_value = [{
            "id_ingreso": 10,
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "patente": "ABC123",
            "en_lavado": 0,
            "noches_prepagadas": [{
                "monto_snapshot": 5000,
                "hora_inicio_snapshot": "22:00",
                "hora_fin_snapshot": "08:00",
            }],
        }]

        resultado = registro_controller.registrar_salida_detallada("ABC123", "admin")

        update_params = next(params for query, params in cursor.executed if "UPDATE ingresos" in query)
        print_job = next(params for query, params in cursor.executed if "INSERT INTO print_jobs" in query)
        self.assertEqual(update_params[1], 1500)
        self.assertEqual(resultado["tarifa"], 1500)
        self.assertEqual(resultado["total_noches_prepagadas"], 5000)
        self.assertEqual(json.loads(print_job[4])["noches_prepagadas"][0]["monto_snapshot"], 5000)

    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_retorna_none_si_no_hay_ingresos_activos(self, db_cursor, obtener_activos):
        obtener_activos.return_value = []

        resultado = registro_controller.registrar_salida("ABC123", "admin")

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()

    @patch.object(registro_controller, "obtener_configuracion")
    @patch.object(registro_controller, "calcular_tarifa")
    @patch.object(registro_controller, "obtener_operacion_convertida_por_ingreso")
    @patch.object(registro_controller, "calcular_minutos_lavado")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registra_salida_calcula_tarifa_y_genera_ticket(
        self,
        db_cursor,
        obtener_activos,
        calcular_minutos_lavado,
        obtener_operacion_convertida,
        calcular_tarifa,
        obtener_configuracion,
    ):
        cursor = FakeCursor()
        db_cursor.return_value = FakeDbCursorContext(cursor)
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        obtener_activos.return_value = [
            {
                "id_ingreso": 10,
                "fecha_hora_ingreso": fecha_ingreso,
                "patente": "ABC123",
                "en_lavado": 0,
            }
        ]
        calcular_minutos_lavado.return_value = 0
        obtener_operacion_convertida.return_value = None
        calcular_tarifa.return_value = (1500, False, 0)
        obtener_configuracion.return_value = {"modo_cobro": "minuto"}

        resultado = registro_controller.registrar_salida_detallada("ABC123", "admin")

        self.assertEqual(resultado["tarifa"], 1500)
        db_cursor.assert_called_once_with(commit=True)
        calcular_tarifa.assert_called_once()
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE ingresos", consultas)
        self.assertIn("fecha_hora_salida IS NULL", consultas)
        print_job = next(
            params for query, params in cursor.executed
            if "INSERT INTO print_jobs" in query
        )
        self.assertEqual(
            print_job[:4], ("TICKET_SALIDA", "PC_PDF", 10, "ABC123")
        )
        self.assertEqual(print_job[5:], ("PENDIENTE", "desktop-salida:10:pc-pdf"))
        self.assertEqual(json.loads(print_job[4]), {
            "kind": "TICKET_SALIDA",
            "id_ingreso": 10,
            "patente": "ABC123",
            "hora_ingreso": "2026-01-01T10:00:00",
            "hora_salida": resultado["fecha_hora_salida"].isoformat(timespec="seconds"),
            "minutos_cobrados": resultado["minutos"],
            "monto_final": 1500,
            "detalle": {
                "texto": None,
                "monto_estacionamiento": 1500,
                "total_lavados": 0,
                "modo_cobro": "minuto",
                "subida_aplicada": False,
                "monto_extra": 0,
                "secciones": None,
            },
            "usuario": {"id_usuario": None, "usuario": "admin", "rol": None},
            "meta": {
                "server_time": resultado["fecha_hora_salida"].isoformat(timespec="seconds"),
                "version": 1,
            },
        })

    @patch.object(registro_controller, "obtener_print_jobs_pc_activos", return_value=False)
    @patch.object(registro_controller, "obtener_configuracion", return_value={"modo_cobro": "minuto"})
    @patch.object(registro_controller, "calcular_tarifa", return_value=(1500, False, 0))
    @patch.object(registro_controller, "calcular_minutos_lavado", return_value=0)
    @patch.object(registro_controller, "obtener_ingreso_activo_priorizado")
    @patch.object(registro_controller, "db_cursor")
    def test_registra_salida_sin_crear_job_cuando_la_impresion_pc_esta_desactivada(
        self, db_cursor, obtener_ingreso, _calcular_minutos_lavado, _calcular_tarifa,
        _obtener_configuracion, _obtener_print_jobs_pc_activos
    ):
        cursor = FakeCursor()
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_ingreso.return_value = {
            "id_ingreso": 10,
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "patente": "ABC123",
            "en_lavado": 0,
        }

        resultado = registro_controller.registrar_salida_detallada("ABC123", "admin")

        self.assertEqual(resultado["tarifa"], 1500)
        self.assertIn("UPDATE ingresos", "\n".join(query for query, _ in cursor.executed))
        self.assertNotIn("INSERT INTO print_jobs", "\n".join(query for query, _ in cursor.executed))

    @patch.object(registro_controller, "obtener_configuracion", return_value={"modo_cobro": "minuto"})
    @patch.object(registro_controller, "calcular_tarifa", return_value=(1500, False, 0))
    @patch.object(registro_controller, "calcular_minutos_lavado", return_value=0)
    @patch.object(registro_controller, "obtener_ingreso_activo_priorizado")
    def test_salida_hace_rollback_si_falla_el_job_durable(
        self,
        obtener_ingreso,
        calcular_minutos_lavado,
        calcular_tarifa,
        obtener_configuracion,
    ):
        cursor = FailingPrintJobCursor()
        connection = FakeConnection(cursor)
        obtener_ingreso.return_value = {
            "id_ingreso": 10,
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "patente": "ABC123",
            "en_lavado": 0,
        }

        with patch.object(registro_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            resultado = registro_controller.registrar_salida("ABC123", "admin")

        self.assertIsNone(resultado)
        self.assertFalse(connection.committed)
        self.assertTrue(connection.rolled_back)
        queries_before_rollback = [
            query for query, _ in connection.executed_before_rollback
        ]
        update_index = next(
            index for index, query in enumerate(queries_before_rollback)
            if "UPDATE ingresos" in query
        )
        print_job_index = next(
            index for index, query in enumerate(queries_before_rollback)
            if "INSERT INTO print_jobs" in query
        )
        self.assertLess(update_index, print_job_index)

    @patch.object(registro_controller, "obtener_configuracion", return_value={"modo_cobro": "minuto"})
    @patch.object(registro_controller, "calcular_tarifa", return_value=(1500, False, 0))
    @patch.object(registro_controller, "calcular_minutos_lavado", return_value=0)
    @patch.object(registro_controller, "obtener_ingreso_activo_priorizado")
    @patch.object(registro_controller, "db_cursor")
    def test_salida_no_crea_job_si_el_ingreso_ya_fue_cerrado(
        self,
        db_cursor,
        obtener_ingreso,
        calcular_minutos_lavado,
        calcular_tarifa,
        obtener_configuracion,
    ):
        cursor = FakeCursor()
        cursor.rowcount = 0
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_ingreso.return_value = {
            "id_ingreso": 10,
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "patente": "ABC123",
            "en_lavado": 0,
        }

        resultado = registro_controller.registrar_salida("ABC123", "admin")

        self.assertIsNone(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("fecha_hora_salida IS NULL", consultas)
        self.assertNotIn("INSERT INTO print_jobs", consultas)

    def test_clave_idempotencia_de_salida_es_estable(self):
        self.assertEqual(salida_idempotency_key(123), "desktop-salida:123:pc-pdf")
        self.assertEqual(salida_idempotency_key(123), salida_idempotency_key(123))

    def test_clave_idempotencia_de_salida_reingresada_es_distinta_y_estable(self):
        self.assertEqual(
            salida_idempotency_key(123, 1),
            "desktop-salida:123:pc-pdf:reingreso:1",
        )
        self.assertEqual(salida_idempotency_key(123, 1), salida_idempotency_key(123, 1))

    def test_helper_crea_un_job_durable_de_salida(self):
        cursor = FakeCursor()
        fecha_ingreso = datetime(2026, 7, 24, 10, 30)
        fecha_salida = datetime(2026, 7, 24, 11, 15)

        crear_print_job_salida(
            cursor,
            123,
            "ABC123",
            fecha_ingreso,
            fecha_salida,
            45,
            3800,
            "45 minutos",
            1800,
            2000,
            "admin",
            modo_cobro="personalizado",
            subida_aplicada=True,
            monto_extra=500,
            secciones={
                "lavado": {
                    "inicio": fecha_ingreso,
                    "fin": fecha_salida,
                    "duracion_minutos": 45,
                    "monto": 2000,
                },
            },
        )

        self.assertEqual(len(cursor.executed), 1)
        query, params = cursor.executed[0]
        self.assertIn("INSERT INTO print_jobs", query)
        self.assertEqual(params[:4], ("TICKET_SALIDA", "PC_PDF", 123, "ABC123"))
        self.assertEqual(params[5:], ("PENDIENTE", "desktop-salida:123:pc-pdf"))
        self.assertEqual(json.loads(params[4])["detalle"], {
            "texto": "45 minutos",
            "monto_estacionamiento": 1800,
            "total_lavados": 2000,
            "modo_cobro": "personalizado",
            "subida_aplicada": True,
            "monto_extra": 500,
            "secciones": {
                "lavado": {
                    "inicio": "2026-07-24T10:30:00",
                    "fin": "2026-07-24T11:15:00",
                    "duracion_minutos": 45,
                    "monto": 2000,
                },
            },
        })

    @patch.object(registro_controller, "obtener_configuracion", return_value={"modo_cobro": "minuto"})
    @patch.object(registro_controller, "calcular_tarifa", return_value=(1500, False, 0))
    @patch.object(registro_controller, "calcular_minutos_lavado", return_value=0)
    @patch.object(registro_controller, "obtener_ingreso_activo_priorizado")
    @patch.object(registro_controller, "db_cursor")
    def test_salida_reingresada_usa_nueva_clave_si_el_job_anterior_fue_cancelado(
        self,
        db_cursor,
        obtener_ingreso,
        _calcular_minutos_lavado,
        _calcular_tarifa,
        _obtener_configuracion,
    ):
        cursor = UniqueSalidaPrintJobCursor("desktop-salida:10:pc-pdf")
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_ingreso.return_value = {
            "id_ingreso": 10,
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "patente": "ABC123",
            "en_lavado": 0,
        }

        resultado = registro_controller.registrar_salida_detallada("ABC123", "admin")

        self.assertEqual(resultado["tarifa"], 1500)
        print_job = next(
            params for query, params in cursor.executed if "INSERT INTO print_jobs" in query
        )
        self.assertEqual(print_job[-1], "desktop-salida:10:pc-pdf:reingreso:1")
        consulta_claves = next(
            query for query, _ in cursor.executed if "SELECT idempotency_key" in query
        )
        self.assertIn("FOR UPDATE", consulta_claves)

    @patch.object(registro_controller, "obtener_configuracion")
    @patch.object(registro_controller, "calcular_tarifa")
    @patch.object(registro_controller, "obtener_operacion_convertida_por_ingreso")
    @patch.object(registro_controller, "calcular_minutos_lavado")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_salida_de_lavado_convertido_detalla_lavado_y_estadia_en_ticket(
        self,
        db_cursor,
        obtener_activos,
        calcular_minutos_lavado,
        obtener_operacion_convertida,
        calcular_tarifa,
        obtener_configuracion,
    ):
        cursor = FakeCursor()
        db_cursor.return_value = FakeDbCursorContext(cursor)
        inicio_lavado = datetime(2026, 1, 1, 9, 30)
        fecha_ingreso = datetime(2026, 1, 1, 10, 0)
        obtener_activos.return_value = [{
            "id_ingreso": 10,
            "fecha_hora_ingreso": fecha_ingreso,
            "patente": "ABC123",
            "en_lavado": 0,
        }]
        calcular_minutos_lavado.return_value = 0
        obtener_operacion_convertida.return_value = {
            "fecha_hora_inicio": inicio_lavado,
            "fecha_hora_fin": fecha_ingreso,
            "valor_lavado_snapshot": 9000,
        }
        calcular_tarifa.return_value = (1500, False, 0)
        obtener_configuracion.return_value = {"modo_cobro": "minuto"}

        resultado = registro_controller.registrar_salida_detallada("ABC123", "admin")

        self.assertEqual(resultado["tarifa"], 10500)
        self.assertEqual(resultado["tarifa_estacionamiento"], 1500)
        self.assertEqual(resultado["total_lavados"], 9000)
        print_job = next(
            params for query, params in cursor.executed
            if "INSERT INTO print_jobs" in query
        )
        self.assertEqual(json.loads(print_job[4])["detalle"]["total_lavados"], 9000)
        detalle = json.loads(print_job[4])["detalle"]
        self.assertEqual(detalle["modo_cobro"], "minuto")
        self.assertFalse(detalle["subida_aplicada"])
        self.assertEqual(detalle["monto_extra"], 0)
        self.assertEqual(detalle["secciones"], {
            "lavado": {
                "inicio": "2026-01-01T09:30:00",
                "fin": "2026-01-01T10:00:00",
                "duracion_minutos": 30,
                "monto": 9000,
            },
            "estadia": {
                "inicio": "2026-01-01T10:00:00",
                "fin": resultado["fecha_hora_salida"].isoformat(),
                "duracion_minutos": resultado["minutos"],
                "monto": 1500,
            },
        })

    @patch.object(registro_controller, "obtener_configuracion")
    @patch.object(registro_controller, "calcular_tarifa")
    @patch.object(registro_controller, "obtener_operacion_convertida_por_ingreso")
    @patch.object(registro_controller, "calcular_total_lavados")
    @patch.object(registro_controller, "calcular_minutos_lavado")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_ingreso_mas_lavado_existente_mantiene_totales_de_ticket_sin_detalle_solo(
        self,
        db_cursor,
        obtener_activos,
        calcular_minutos_lavado,
        calcular_total_lavados,
        obtener_operacion_convertida,
        calcular_tarifa,
        obtener_configuracion,
    ):
        cursor = FakeCursor()
        db_cursor.return_value = FakeDbCursorContext(cursor)
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        obtener_activos.return_value = [{
            "id_ingreso": 10,
            "fecha_hora_ingreso": fecha_ingreso,
            "patente": "ABC123",
            "en_lavado": 0,
        }]
        calcular_minutos_lavado.return_value = 20
        calcular_total_lavados.return_value = 8000
        obtener_operacion_convertida.return_value = None
        calcular_tarifa.return_value = (1500, False, 0)
        obtener_configuracion.return_value = {"modo_cobro": "minuto"}

        resultado = registro_controller.registrar_salida_detallada("ABC123", "admin")

        self.assertEqual(resultado["tarifa"], 9500)
        self.assertEqual(resultado["tarifa_estacionamiento"], 1500)
        self.assertEqual(resultado["total_lavados"], 8000)
        print_job = next(
            params for query, params in cursor.executed
            if "INSERT INTO print_jobs" in query
        )
        self.assertEqual(json.loads(print_job[4])["detalle"]["total_lavados"], 8000)

    @patch.object(registro_controller, "obtener_configuracion")
    @patch.object(registro_controller, "calcular_tarifa")
    @patch.object(registro_controller, "calcular_minutos_lavado")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registrar_salida_detallada_retorna_horas_minutos_y_tarifa(
        self,
        db_cursor,
        obtener_activos,
        calcular_minutos_lavado,
        calcular_tarifa,
        obtener_configuracion,
    ):
        cursor = FakeCursor()
        db_cursor.return_value = FakeDbCursorContext(cursor)
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        obtener_activos.return_value = [
            {
                "id_ingreso": 10,
                "fecha_hora_ingreso": fecha_ingreso,
                "patente": "ABC123",
                "en_lavado": 0,
            }
        ]
        calcular_minutos_lavado.return_value = 0
        calcular_tarifa.return_value = (1500, False, 0)
        obtener_configuracion.return_value = {"modo_cobro": "minuto"}

        resultado = registro_controller.registrar_salida_detallada("ABC123", "admin")

        self.assertEqual(resultado["patente"], "ABC123")
        self.assertEqual(resultado["fecha_hora_ingreso"], fecha_ingreso)
        self.assertIsInstance(resultado["fecha_hora_salida"], datetime)
        self.assertIsInstance(resultado["minutos"], int)
        self.assertEqual(resultado["tarifa"], 1500)
        self.assertIn(
            "INSERT INTO print_jobs",
            "\n".join(query for query, _ in cursor.executed),
        )

    @patch.object(registro_controller, "datetime")
    @patch("controllers.tarifas_controller.obtener_subida_activa", return_value=None)
    @patch("controllers.tarifas_controller.obtener_configuracion")
    @patch.object(registro_controller, "obtener_configuracion")
    @patch.object(registro_controller, "obtener_operacion_convertida_por_ingreso", return_value=None)
    @patch.object(registro_controller, "calcular_total_lavados", return_value=0)
    @patch.object(registro_controller, "calcular_minutos_lavado")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    def test_registra_salida_y_crea_job_si_falla_lectura_del_toggle_pc(
        self,
        obtener_activos,
        calcular_minutos_lavado,
        calcular_total_lavados,
        obtener_operacion_convertida,
        obtener_configuracion,
        obtener_configuracion_tarifa,
        _obtener_subida_activa,
        datetime_mock,
    ):
        cursor = FailingConfigLookupCursor()
        connection = FakeConnection(cursor)
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        obtener_activos.return_value = [
            {
                "id_ingreso": 10,
                "fecha_hora_ingreso": fecha_ingreso,
                "patente": "ABC123",
                "en_lavado": 0,
            }
        ]
        calcular_minutos_lavado.return_value = 0
        config_tarifa = {
            "modo_cobro": "minuto",
            "tarifa_minima": "300",
            "valor_minuto": "25",
        }
        obtener_configuracion.return_value = config_tarifa
        obtener_configuracion_tarifa.return_value = config_tarifa
        datetime_mock.now.return_value = datetime(2026, 1, 1, 10, 30, 0)

        with patch.object(registro_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            resultado = registro_controller.registrar_salida("ABC123", "admin")

        self.assertEqual(resultado, 1025)
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE ingresos", consultas)
        self.assertIn("FROM configuracion", consultas)
        self.assertIn("INSERT INTO print_jobs", consultas)

    @patch("controllers.tarifas_controller.obtener_configuracion")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_registra_salida_si_falla_la_configuracion_tarifaria(
        self,
        db_cursor,
        obtener_activos,
        obtener_configuracion_tarifa,
    ):
        obtener_activos.return_value = [{
            "id_ingreso": 10,
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0, 0),
            "patente": "ABC123",
            "en_lavado": 0,
        }]
        obtener_configuracion_tarifa.side_effect = RuntimeError("configuracion tarifaria no disponible")

        resultado = registro_controller.registrar_salida("ABC123", "admin")

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()


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

    def _ingreso_cerrado_reversible(self, cerrado=0):
        return {
            "id_ingreso": 10,
            "id_vehiculo": 7,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "fecha_hora_salida": datetime(2026, 1, 1, 11, 0),
            "tarifa_aplicada": 1500,
            "usuario": "operador-salida",
            "cerrado": cerrado,
        }

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_exige_confirmacion_pero_no_motivo(self, db_cursor):
        sin_confirmacion = registro_controller.reingresar_vehiculo_cerrado(10, "admin")

        self.assertFalse(sin_confirmacion[0])
        self.assertIn("confirmar", sin_confirmacion[1])
        db_cursor.assert_not_called()

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_revierte_el_mismo_ingreso_y_audita_sin_motivo(self, db_cursor):
        ingreso = self._ingreso_cerrado_reversible()
        cursor = FakeCursor(fetchone_results=[ingreso, None], fetchall_results=[[]])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10, "operador-reversion", True)

        self.assertEqual(resultado[0], True)
        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO ingresos", consultas)
        self.assertIn("INSERT INTO reversiones_salida", consultas)
        self.assertNotIn("CREATE TABLE", consultas)
        self.assertNotIn("ALTER TABLE", consultas)
        self.assertTrue(all(
            query.lstrip().upper().startswith(("SELECT", "UPDATE", "INSERT"))
            for query, _ in cursor.executed
        ))
        self.assertIn("fecha_hora_salida = NULL", consultas)
        self.assertIn("tarifa_aplicada = NULL", consultas)
        self.assertIn("FROM vehiculos", consultas)
        self.assertNotIn("SET reingresado = 1", consultas)
        update_params = next(params for query, params in cursor.executed if "fecha_hora_salida = NULL" in query)
        self.assertEqual(update_params, (10,))
        audit_params = next(params for query, params in cursor.executed if "INSERT INTO reversiones_salida" in query)
        self.assertEqual(audit_params[:7], (
            10, "ABC123", ingreso["fecha_hora_ingreso"], ingreso["fecha_hora_salida"],
            1500, "operador-salida", "operador-reversion",
        ))
        self.assertEqual(audit_params[7], "No informado")

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_usa_motivo_por_defecto_si_es_vacio_o_espacios(self, db_cursor):
        for motivo in ("", "   "):
            with self.subTest(motivo=repr(motivo)):
                cursor = FakeCursor(
                    fetchone_results=[self._ingreso_cerrado_reversible(), None],
                    fetchall_results=[[]],
                )
                db_cursor.return_value = FakeDbCursorContext(cursor)

                resultado = registro_controller.reingresar_vehiculo_cerrado(
                    10, "operador-reversion", True, motivo
                )

                self.assertTrue(resultado[0])
                audit_params = next(
                    params
                    for query, params in cursor.executed
                    if "INSERT INTO reversiones_salida" in query
                )
                self.assertEqual(audit_params[7], "No informado")

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_rechaza_si_el_cierre_diario_ya_lo_incluyo(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[self._ingreso_cerrado_reversible(cerrado=1)])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10, "admin", True, "Sin cobro.")

        self.assertFalse(resultado[0])
        self.assertIn("cierre diario", resultado[1])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO reversiones_salida", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_rechaza_si_ya_existe_un_ingreso_activo(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[self._ingreso_cerrado_reversible(), None, {"id_ingreso": 12}])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10, "admin", True, "Sin cobro.")

        self.assertFalse(resultado[0])
        self.assertIn("ingreso activo", resultado[1])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO reversiones_salida", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_consumes_vehicle_lock_result_before_next_query(self, db_cursor):
        cursor = VehicleLockResultCursor(
            fetchone_results=[self._ingreso_cerrado_reversible(), (7,), None],
            fetchall_results=[[]],
        )
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10, "admin", True)

        self.assertTrue(resultado[0])
        self.assertTrue(any(
            "WHERE id_vehiculo = %s" in query
            for query, _ in cursor.executed
        ))

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_cancela_solo_jobs_salida_reintentables(self, db_cursor):
        jobs = [
            {"id_print_job": 1, "estado": "PENDIENTE"},
            {"id_print_job": 2, "estado": "ERROR"},
            {"id_print_job": 3, "estado": "REVISION_MANUAL"},
        ]
        cursor = FakeCursor(fetchone_results=[self._ingreso_cerrado_reversible(), None], fetchall_results=[jobs])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10, "admin", True, "Sin cobro.")

        self.assertTrue(resultado[0])
        cancel_query, cancel_params = next(
            (query, params) for query, params in cursor.executed if "SET estado = 'CANCELADO'" in query
        )
        self.assertIn("tipo = 'TICKET_SALIDA'", cancel_query)
        self.assertIn("'PENDIENTE', 'ERROR', 'REVISION_MANUAL'", cancel_query)
        self.assertEqual(cancel_params, (10,))

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_bloquea_ticket_salida_imprimiendo(self, db_cursor):
        cursor = FakeCursor(
            fetchone_results=[self._ingreso_cerrado_reversible(), None],
            fetchall_results=[[{"id_print_job": 5, "estado": "IMPRIMIENDO"}]],
        )
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10, "admin", True, "Sin cobro.")

        self.assertFalse(resultado[0])
        self.assertIn("imprime", resultado[1])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("SET estado = 'CANCELADO'", consultas)
        self.assertNotIn("INSERT INTO reversiones_salida", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_exige_confirmacion_para_ticket_impreso(self, db_cursor):
        jobs = [{"id_print_job": 5, "estado": "IMPRESO"}]
        cursor = FakeCursor(fetchone_results=[self._ingreso_cerrado_reversible(), None], fetchall_results=[jobs])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(10, "admin", True, "Sin cobro.")

        self.assertFalse(resultado[0])
        self.assertIn("confirmación explícita", resultado[1])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO reversiones_salida", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_reingresar_vehiculo_cerrado_audita_confirmacion_de_ticket_impreso(self, db_cursor):
        jobs = [{"id_print_job": 5, "estado": "IMPRESO"}]
        cursor = FakeCursor(fetchone_results=[self._ingreso_cerrado_reversible(), None], fetchall_results=[jobs])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.reingresar_vehiculo_cerrado(
            10, "admin", True, "Sin cobro.", True
        )

        self.assertTrue(resultado[0])
        audit_params = next(params for query, params in cursor.executed if "INSERT INTO reversiones_salida" in query)
        self.assertTrue(audit_params[-1])
        self.assertIn('"estado": "IMPRESO"', audit_params[-2])

    def test_reingresar_vehiculo_cerrado_continua_si_falla_la_auditoria(self):
        cursor = FailingSalidaReversalAuditCursor(
            fetchone_results=[self._ingreso_cerrado_reversible(), None], fetchall_results=[[]]
        )
        connection = FakeConnection(cursor)

        with patch.object(registro_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            resultado = registro_controller.reingresar_vehiculo_cerrado(
                10, "admin", True, "Sin cobro."
            )

        self.assertTrue(resultado[0])
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO reversiones_salida", consultas)
        self.assertIn("fecha_hora_salida = NULL", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_envia_salida_sin_cobro_a_espera_y_audita_la_salida_original(self, db_cursor):
        ingreso = self._ingreso_cerrado_reversible()
        cursor = FakeCursor(fetchone_results=[ingreso, None], fetchall_results=[[]])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.enviar_salida_sin_cobro_a_espera(10, "admin", True)

        self.assertTrue(resultado[0])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("en_espera = 1", consultas)
        self.assertIn("fecha_hora_salida = NULL", consultas)
        self.assertIn("tarifa_aplicada = NULL", consultas)
        self.assertIn("INSERT INTO reversiones_salida", consultas)
        audit_params = next(params for query, params in cursor.executed if "INSERT INTO reversiones_salida" in query)
        self.assertEqual(audit_params[7], "Salida sin cobro enviada a espera para revisión administrativa.")

    @patch.object(registro_controller, "db_cursor")
    def test_no_envia_a_espera_salida_incluida_en_cierre_diario(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[self._ingreso_cerrado_reversible(cerrado=1)])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.enviar_salida_sin_cobro_a_espera(10, "admin", True)

        self.assertFalse(resultado[0])
        self.assertIn("cierre diario", resultado[1])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("UPDATE ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_envio_a_espera_exige_confirmacion_para_ticket_impreso(self, db_cursor):
        cursor = FakeCursor(
            fetchone_results=[self._ingreso_cerrado_reversible(), None],
            fetchall_results=[[{"id_print_job": 5, "estado": "IMPRESO"}]],
        )
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.enviar_salida_sin_cobro_a_espera(10, "admin", True)

        self.assertFalse(resultado[0])
        self.assertIn("confirmación explícita", resultado[1])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("UPDATE ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_envio_a_espera_limpia_campos_que_caja_y_reportes_usan_para_contar_salidas(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[self._ingreso_cerrado_reversible(), None], fetchall_results=[[]])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        registro_controller.enviar_salida_sin_cobro_a_espera(10, "admin", True)

        update_query = next(query for query, _ in cursor.executed if "UPDATE ingresos" in query)
        self.assertIn("fecha_hora_salida = NULL", update_query)
        self.assertIn("tarifa_aplicada = NULL", update_query)

    @patch.object(registro_controller, "db_cursor")
    def test_envio_a_espera_revalida_la_patente_del_ingreso_seleccionado(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[self._ingreso_cerrado_reversible()])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.enviar_salida_sin_cobro_a_espera(
            10, "operador", True, patente_esperada="OTRA123"
        )

        self.assertFalse(resultado[0])
        self.assertIn("no coincide", resultado[1])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("UPDATE ingresos", consultas)

    def test_envio_a_espera_revierte_si_no_se_puede_auditar_la_salida(self):
        cursor = FailingSalidaReversalAuditCursor(
            fetchone_results=[self._ingreso_cerrado_reversible(), None], fetchall_results=[[]]
        )
        connection = FakeConnection(cursor)

        with patch.object(registro_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            resultado = registro_controller.enviar_salida_sin_cobro_a_espera(10, "admin", True)

        self.assertFalse(resultado[0])
        self.assertFalse(connection.committed)
        self.assertTrue(connection.rolled_back)

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
        self.assertIn("i.cerrado = FALSE", consultas)

    @patch.object(registro_controller, "asegurar_schema_lavados")
    @patch.object(registro_controller, "obtener_minutos_lavado_por_ingresos")
    @patch.object(registro_controller, "obtener_contexto_tarifa")
    @patch.object(registro_controller, "calcular_tarifa_con_contexto")
    @patch.object(registro_controller, "db_cursor")
    def test_obtener_vehiculos_activos_formatea_activos_y_calcula_montos(
        self,
        db_cursor,
        calcular_tarifa_con_contexto,
        obtener_contexto_tarifa,
        obtener_minutos_lavado_por_ingresos,
        asegurar_schema,
    ):
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        filas = [
            {
                "id_ingreso": 1,
                "patente": "ABC123",
                "fecha_hora_ingreso": fecha_ingreso,
                "en_espera": 0,
                "en_lavado": 0,
            },
            {
                "id_ingreso": 2,
                "patente": "XYZ789",
                "fecha_hora_ingreso": fecha_ingreso,
                "en_espera": 1,
                "en_lavado": 0,
            },
        ]
        cursor = FakeCursor(fetchall_results=[filas])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        contexto = {"config": {"modo_cobro": "minuto"}, "subida": None, "tramos": []}
        obtener_contexto_tarifa.return_value = contexto
        obtener_minutos_lavado_por_ingresos.return_value = {1: 0, 2: 0}
        calcular_tarifa_con_contexto.return_value = 1200

        resultado = registro_controller.obtener_vehiculos_activos()

        db_cursor.assert_called_once_with(dictionary=True)
        obtener_contexto_tarifa.assert_called_once()
        obtener_minutos_lavado_por_ingresos.assert_called_once()
        calcular_tarifa_con_contexto.assert_called_once()
        self.assertIs(calcular_tarifa_con_contexto.call_args.args[3], contexto)
        self.assertEqual(resultado[0]["patente"], "ABC123")
        self.assertEqual(resultado[0]["monto"], 1200)
        self.assertEqual(resultado[1]["patente"], "XYZ789 [EN ESPERA]")
        self.assertEqual(resultado[1]["monto"], 0)
        self.assertTrue(resultado[1]["en_espera"])

    @patch.object(registro_controller, "asegurar_schema_lavados")
    @patch.object(registro_controller, "obtener_minutos_lavado_por_ingresos")
    @patch.object(registro_controller, "obtener_contexto_tarifa")
    @patch.object(registro_controller, "calcular_tarifa_con_contexto")
    @patch.object(registro_controller, "db_cursor")
    def test_obtener_vehiculos_activos_reutiliza_contexto_tarifa_para_multiples_vehiculos(
        self,
        db_cursor,
        calcular_tarifa_con_contexto,
        obtener_contexto_tarifa,
        obtener_minutos_lavado_por_ingresos,
        asegurar_schema,
    ):
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        filas = [
            {
                "id_ingreso": index,
                "patente": f"ABC{index}",
                "fecha_hora_ingreso": fecha_ingreso,
                "en_espera": 0,
                "en_lavado": 0,
            }
            for index in range(1, 6)
        ]
        cursor = FakeCursor(fetchall_results=[filas])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        contexto = {"config": {"modo_cobro": "minuto"}, "subida": None, "tramos": []}
        obtener_contexto_tarifa.return_value = contexto
        obtener_minutos_lavado_por_ingresos.return_value = {index: 0 for index in range(1, 6)}
        calcular_tarifa_con_contexto.return_value = 1200

        resultado = registro_controller.obtener_vehiculos_activos()

        self.assertEqual(len(resultado), 5)
        obtener_contexto_tarifa.assert_called_once()
        self.assertEqual(calcular_tarifa_con_contexto.call_count, 5)
        for call in calcular_tarifa_con_contexto.call_args_list:
            self.assertIs(call.args[3], contexto)

    @patch.object(registro_controller, "asegurar_schema_lavados")
    @patch.object(registro_controller, "obtener_minutos_lavado_por_ingresos")
    @patch.object(registro_controller, "obtener_contexto_tarifa")
    @patch.object(registro_controller, "calcular_tarifa_con_contexto")
    @patch.object(registro_controller, "db_cursor")
    def test_obtener_vehiculos_activos_descuenta_minutos_de_lavado_y_muestra_estado(
        self,
        db_cursor,
        calcular_tarifa_con_contexto,
        obtener_contexto_tarifa,
        obtener_minutos_lavado_por_ingresos,
        asegurar_schema,
    ):
        fecha_ingreso = datetime(2026, 1, 1, 10, 0, 0)
        filas = [{
            "id_ingreso": 1,
            "patente": "ABC123",
            "fecha_hora_ingreso": fecha_ingreso,
            "en_espera": 0,
            "en_lavado": 1,
        }]
        cursor = FakeCursor(fetchall_results=[filas])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        contexto = {"config": {"modo_cobro": "minuto"}, "subida": None, "tramos": []}
        obtener_contexto_tarifa.return_value = contexto
        obtener_minutos_lavado_por_ingresos.return_value = {1: 15}
        calcular_tarifa_con_contexto.return_value = 1200

        resultado = registro_controller.obtener_vehiculos_activos()

        self.assertIn("[EN LAVADO]", resultado[0]["patente"])
        self.assertTrue(resultado[0]["en_lavado"])
        self.assertGreaterEqual(resultado[0]["minutos"], 0)

    @patch.object(registro_controller, "db_cursor")
    def test_obtener_total_vehiculos_pagados_turno_actual_suma_no_cerrados(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[{"total": 3500}])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.obtener_total_vehiculos_pagados_turno_actual()

        self.assertEqual(resultado, 3500.0)
        db_cursor.assert_called_once_with(dictionary=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("SUM(tarifa_aplicada)", consultas)
        self.assertIn("fecha_hora_salida IS NOT NULL", consultas)
        self.assertIn("cerrado = FALSE", consultas)
        self.assertIn("FROM ingresos_eliminados", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_obtener_total_vehiculos_pagados_turno_actual_retorna_cero_si_no_hay_total(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[{"total": None}])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.obtener_total_vehiculos_pagados_turno_actual()

        self.assertEqual(resultado, 0.0)

    @patch.object(registro_controller, "db_cursor")
    def test_obtener_resumen_caja_actual_incluye_cada_ingreso_pendiente_de_cierre(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[
            [{"tarifa_aplicada": 1200}],
            [{"monto": 300}],
            [
                {"estado": "FINALIZADO_COBRADO", "valor_lavado_snapshot": 8000},
                {"estado": "CONVERTIDO_ESTADIA", "valor_lavado_snapshot": 9000},
            ],
            [{"monto_snapshot": 50000}],
            [{"monto_snapshot": 5000}],
            [],
        ])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resumen = registro_controller.obtener_resumen_caja_actual()

        self.assertEqual(resumen["total_recaudado"], 1200)
        self.assertEqual(resumen["total_banos_monto"], 300)
        self.assertEqual(resumen["total_lavados_solos_monto"], 8000)
        self.assertEqual(resumen["total_mensualidades_monto"], 50000)
        self.assertEqual(resumen["total_noches_monto"], 5000)
        self.assertEqual(resumen["total_general"], 64500)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("fecha_hora_salida IS NOT NULL", consultas)
        self.assertIn("estado = 'FINALIZADO_COBRADO'", consultas)
        self.assertIn("id_cierre IS NULL", consultas)
        self.assertIn("estado = 'PAGADO'", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_obtener_resumen_caja_actual_resta_gastos_pendientes_sin_alterar_bruto(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[
            [{"tarifa_aplicada": 1000}], [], [], [], [], [{"monto": 450}],
        ])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resumen = registro_controller.obtener_resumen_caja_actual()

        self.assertEqual(resumen["total_general"], 1000)
        self.assertEqual(resumen["total_gastos"], 450)
        self.assertEqual(resumen["total_neto"], 550)

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
        self.assertIn("FROM ingresos_eliminados", consultas)

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
    def test_eliminar_ingreso_con_respaldo_desvincula_jobs_respalda_y_elimina(self, db_cursor):
        ingreso = {
            "id_ingreso": 10,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "fecha_hora_salida": None,
            "en_espera": 1,
        }
        cursor = FakeCursor(fetchone_results=[ingreso, None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        self.assertEqual(resultado, (True, "Ingreso en espera eliminado correctamente."))
        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE print_jobs", consultas)
        self.assertIn("estado = 'CANCELADO'", consultas)
        self.assertIn("INSERT INTO ingresos_eliminados", consultas)
        self.assertIn("DELETE FROM ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_eliminar_ingreso_revertido_lo_anula_y_conserva_su_auditoria(self, db_cursor):
        ingreso = {
            "id_ingreso": 10,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "fecha_hora_salida": None,
            "en_espera": 1,
        }
        cursor = FakeCursor(fetchone_results=[ingreso, {"existe": 1}])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        self.assertEqual(resultado, (True, "Ingreso en espera anulado correctamente."))
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM reversiones_salida", consultas)
        self.assertIn("INSERT INTO ingresos_eliminados", consultas)
        self.assertIn("SET en_espera = 0", consultas)
        self.assertNotIn("SET id_ingreso = NULL", consultas)
        self.assertNotIn("DELETE FROM ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_eliminar_ingreso_con_respaldo_bloquea_job_imprimiendo(self, db_cursor):
        ingreso = {
            "id_ingreso": 10,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "fecha_hora_salida": None,
            "en_espera": 1,
        }
        cursor = FakeCursor(
            fetchone_results=[ingreso],
            fetchall_results=[[{"id_print_job": 5, "estado": "IMPRIMIENDO"}]],
        )
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        self.assertFalse(resultado[0])
        self.assertIn("imprimiendo", resultado[1])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("SELECT id_print_job, estado", consultas)
        self.assertNotIn("estado = 'CANCELADO'", consultas)
        self.assertNotIn("DELETE FROM ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_eliminar_ingreso_con_respaldo_cancela_jobs_reintentables_y_preserva_terminales(self, db_cursor):
        ingreso = {
            "id_ingreso": 10,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "fecha_hora_salida": None,
            "en_espera": 1,
        }
        cursor = FakeCursor(fetchone_results=[ingreso, None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        self.assertTrue(resultado[0])
        cancel_query, cancel_params = next(
            (query, params) for query, params in cursor.executed
            if "SET estado = 'CANCELADO'" in query
        )
        self.assertIn("'PENDIENTE', 'ERROR', 'REVISION_MANUAL'", cancel_query)
        self.assertEqual(cancel_params, (10,))
        unlink_query, unlink_params = next(
            (query, params) for query, params in cursor.executed
            if "SET id_ingreso = NULL" in query
        )
        self.assertNotIn("estado", unlink_query.lower().split("set", 1)[1])
        self.assertEqual(unlink_params, (10,))

    @patch.object(registro_controller, "db_cursor")
    def test_eliminar_ingreso_con_respaldo_no_elimina_si_no_existe_ingreso(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[None])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        self.assertEqual(resultado, (False, "El ingreso ya no existe."))
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("UPDATE print_jobs", consultas)
        self.assertNotIn("INSERT INTO ingresos_eliminados", consultas)
        self.assertNotIn("DELETE FROM ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_eliminar_ingreso_con_respaldo_no_elimina_ingreso_normal_activo(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[{
            "id_ingreso": 10,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "fecha_hora_salida": None,
            "en_espera": 0,
        }])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        self.assertEqual(resultado, (False, "Solo se pueden eliminar ingresos abiertos en espera."))
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("UPDATE print_jobs", consultas)
        self.assertNotIn("DELETE FROM ingresos", consultas)

    @patch.object(registro_controller, "db_cursor")
    def test_eliminar_ingreso_con_respaldo_no_elimina_ingreso_cerrado(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[{
            "id_ingreso": 10,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "fecha_hora_salida": datetime(2026, 1, 1, 11, 0),
            "en_espera": 1,
        }])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        self.assertEqual(resultado, (False, "No se puede eliminar un ingreso cerrado."))
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("UPDATE print_jobs", consultas)
        self.assertNotIn("DELETE FROM ingresos", consultas)

    def test_eliminar_ingreso_con_respaldo_revierte_si_no_puede_desvincular_print_jobs(self):
        cursor = FailingPrintJobUnlinkCursor(fetchone_results=[{
            "id_ingreso": 10,
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 1, 1, 10, 0),
            "fecha_hora_salida": None,
            "en_espera": 1,
        }])
        connection = FakeConnection(cursor)

        with patch.object(registro_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            resultado = registro_controller.eliminar_ingreso_con_respaldo(10, "admin")

        self.assertFalse(resultado[0])
        self.assertIn("dependencias", resultado[1])
        self.assertFalse(connection.committed)
        self.assertTrue(connection.rolled_back)
        consultas = "\n".join(query for query, _ in connection.executed_before_rollback)
        self.assertIn("UPDATE print_jobs", consultas)
        self.assertNotIn("INSERT INTO ingresos_eliminados", consultas)
        self.assertNotIn("DELETE FROM ingresos", consultas)

    @patch.object(registro_controller, "eliminar_ingreso_con_respaldo")
    @patch.object(registro_controller, "db_cursor")
    def test_eliminar_ingreso_activo_por_patente_selecciona_espera_aunque_haya_un_activo_normal(
        self, db_cursor, eliminar_ingreso
    ):
        cursor = FakeCursor(fetchone_results=[{"id_ingreso": 20}])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        eliminar_ingreso.return_value = (
            False, "Solo se pueden eliminar ingresos abiertos en espera."
        )

        resultado = registro_controller.eliminar_ingreso_activo_por_patente("ABC123", "admin")

        self.assertEqual(resultado, eliminar_ingreso.return_value)
        eliminar_ingreso.assert_called_once_with(20, "admin")
        consulta, params = cursor.executed[0]
        self.assertIn("i.en_espera = 1", consulta)
        self.assertIn("i.fecha_hora_salida IS NULL", consulta)
        self.assertIn("ORDER BY i.fecha_hora_ingreso DESC, i.id_ingreso DESC", consulta)
        self.assertEqual(params, ("ABC123",))

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
