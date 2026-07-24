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


class RegistrarIngresoTests(unittest.TestCase):
    @patch.object(registro_controller, "enqueue_ticket_job")
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
        db_cursor.assert_called_once_with(commit=True)
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

    @patch.object(registro_controller, "enqueue_ticket_job")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_registrar_ingreso_no_encola_ticket_local(
        self,
        db_cursor,
        obtener_activos,
        enqueue_ticket_job,
    ):
        cursor = FakeCursor(fetchone_results=[(77,)])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_activos.return_value = []

        resultado = registro_controller.registrar_ingreso("ABC123")

        self.assertTrue(resultado)
        enqueue_ticket_job.assert_not_called()

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

    @patch.object(registro_controller, "enqueue_ticket_job")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_registra_ingreso_personalizado_futuro(
        self,
        db_cursor,
        obtener_activos,
        generar_ticket,
    ):
        obtener_activos.return_value = []
        fecha_futura = datetime.now() + timedelta(minutes=5)

        resultado = registro_controller.registrar_ingreso_detallado("ABC123", fecha_futura)

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()
        generar_ticket.assert_not_called()

    @patch.object(registro_controller, "enqueue_ticket_job")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_registra_ingreso_personalizado_mayor_a_cuatro_horas(
        self,
        db_cursor,
        obtener_activos,
        generar_ticket,
    ):
        obtener_activos.return_value = []
        fecha_antigua = datetime.now() - timedelta(hours=4, minutes=1)

        resultado = registro_controller.registrar_ingreso_detallado("ABC123", fecha_antigua)

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()
        generar_ticket.assert_not_called()

    @patch.object(registro_controller, "enqueue_ticket_job")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_registra_ingreso_personalizado_de_dia_anterior(
        self,
        db_cursor,
        obtener_activos,
        generar_ticket,
    ):
        obtener_activos.return_value = []
        fecha_anterior = datetime.now() - timedelta(days=1)

        resultado = registro_controller.registrar_ingreso_detallado("ABC123", fecha_anterior)

        self.assertIsNone(resultado)
        db_cursor.assert_not_called()
        generar_ticket.assert_not_called()


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

    @patch.object(registro_controller, "enqueue_ticket_job")
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
        enqueue_ticket_job,
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
        enqueue_ticket_job.assert_not_called()
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

    @patch.object(registro_controller, "obtener_configuracion")
    @patch.object(registro_controller, "calcular_tarifa")
    @patch.object(registro_controller, "calcular_minutos_lavado")
    @patch.object(registro_controller, "obtener_ingresos_activos_por_patente")
    @patch.object(registro_controller, "db_cursor")
    def test_no_actualiza_salida_si_falla_obtener_configuracion(
        self,
        db_cursor,
        obtener_activos,
        calcular_minutos_lavado,
        calcular_tarifa,
        obtener_configuracion,
    ):
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
        obtener_configuracion.side_effect = RuntimeError("config no disponible")

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

    @patch.object(registro_controller, "db_cursor")
    def test_obtener_total_vehiculos_pagados_turno_actual_retorna_cero_si_no_hay_total(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[{"total": None}])
        db_cursor.return_value = FakeDbCursorContext(cursor)

        resultado = registro_controller.obtener_total_vehiculos_pagados_turno_actual()

        self.assertEqual(resultado, 0.0)

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
