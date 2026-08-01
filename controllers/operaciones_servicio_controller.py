from datetime import datetime

import mysql.connector

from controllers.wash_pricing_controller import (
    SOLO_LAVADO_PRICE_CONFIG_MESSAGE,
    build_wash_price_snapshot,
    ensure_wash_vehicle_type_table,
)
from utils.db import db_cursor
from utils.plates import requerir_patente_valida
from utils.print_jobs import crear_print_job_solo_lavado
from controllers.config_controller import obtener_print_jobs_pc_activos


ESTADO_ACTIVO = "ACTIVO"
ESTADO_FINALIZADO_COBRADO = "FINALIZADO_COBRADO"
ESTADO_CONVERTIDO_ESTADIA = "CONVERTIDO_ESTADIA"

_ESTADOS_FINALES = {ESTADO_FINALIZADO_COBRADO, ESTADO_CONVERTIDO_ESTADIA}
_SCHEMA_ENSURED = False
_DUPLICATE_SCHEMA_ERROR_CODES = {1060, 1061}
SOLO_LAVADO_SCHEMA_ERROR_MESSAGE = (
    "No se pudo preparar la base de datos para Solo lavado. "
    "Verificá permisos de ALTER/CREATE y que la actualización de BD se haya aplicado."
)


def _execute_schema(cursor, statement):
    try:
        cursor.execute(statement)
    except mysql.connector.Error as exc:
        if getattr(exc, "errno", None) in _DUPLICATE_SCHEMA_ERROR_CODES:
            return
        raise


def asegurar_schema_operaciones_servicio():
    """Crea/actualiza columnas requeridas por Solo lavado en bases ya desplegadas."""
    global _SCHEMA_ENSURED
    if _SCHEMA_ENSURED:
        return

    try:
        with db_cursor(commit=True) as cursor:
            _execute_schema(cursor, """
                CREATE TABLE IF NOT EXISTS operaciones_servicio (
                    id_operacion_servicio INT AUTO_INCREMENT PRIMARY KEY,
                    patente VARCHAR(10) NOT NULL,
                    id_tipo_vehiculo_lavado INT NULL,
                    tipo_vehiculo_lavado_snapshot VARCHAR(80) NOT NULL,
                    valor_lavado_snapshot INT NOT NULL,
                    fecha_hora_inicio DATETIME NOT NULL,
                    fecha_hora_fin DATETIME NULL,
                    duracion_minutos INT NULL,
                    usuario_inicio VARCHAR(50) NOT NULL,
                    usuario_fin VARCHAR(50) NULL,
                    estado ENUM('ACTIVO', 'FINALIZADO_COBRADO', 'CONVERTIDO_ESTADIA') NOT NULL DEFAULT 'ACTIVO',
                    id_ingreso_generado INT NULL,
                    cerrado TINYINT(1) NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_operaciones_servicio_estado_fecha (estado, fecha_hora_inicio),
                    INDEX idx_operaciones_servicio_patente (patente),
                    INDEX idx_operaciones_servicio_ingreso_generado (id_ingreso_generado),
                    INDEX idx_operaciones_servicio_cierre (cerrado, estado, fecha_hora_fin)
                )
            """)
            for statement in [
                "ALTER TABLE operaciones_servicio ADD COLUMN id_tipo_vehiculo_lavado INT NULL",
                "ALTER TABLE operaciones_servicio ADD COLUMN tipo_vehiculo_lavado_snapshot VARCHAR(80) NULL",
                "ALTER TABLE operaciones_servicio ADD COLUMN valor_lavado_snapshot INT NOT NULL DEFAULT 0",
                "ALTER TABLE operaciones_servicio ADD COLUMN fecha_hora_fin DATETIME NULL",
                "ALTER TABLE operaciones_servicio ADD COLUMN duracion_minutos INT NULL",
                "ALTER TABLE operaciones_servicio ADD COLUMN usuario_fin VARCHAR(50) NULL",
                "ALTER TABLE operaciones_servicio ADD COLUMN estado ENUM('ACTIVO', 'FINALIZADO_COBRADO', 'CONVERTIDO_ESTADIA') NOT NULL DEFAULT 'ACTIVO'",
                "ALTER TABLE operaciones_servicio ADD COLUMN id_ingreso_generado INT NULL",
                "ALTER TABLE operaciones_servicio ADD COLUMN cerrado TINYINT(1) NOT NULL DEFAULT 0",
                "ALTER TABLE operaciones_servicio ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE operaciones_servicio ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
                "ALTER TABLE operaciones_servicio ADD INDEX idx_operaciones_servicio_estado_fecha (estado, fecha_hora_inicio)",
                "ALTER TABLE operaciones_servicio ADD INDEX idx_operaciones_servicio_patente (patente)",
                "ALTER TABLE operaciones_servicio ADD INDEX idx_operaciones_servicio_ingreso_generado (id_ingreso_generado)",
                "ALTER TABLE operaciones_servicio ADD INDEX idx_operaciones_servicio_cierre (cerrado, estado, fecha_hora_fin)",
                "ALTER TABLE cierres_diarios ADD COLUMN total_lavados_solos INT NOT NULL DEFAULT 0",
                "ALTER TABLE cierres_diarios ADD COLUMN total_lavados_solos_monto INT NOT NULL DEFAULT 0",
                "ALTER TABLE cierres_diarios ADD COLUMN total_general INT NOT NULL DEFAULT 0",
            ]:
                _execute_schema(cursor, statement)
    except RuntimeError as exc:
        if str(exc) == SOLO_LAVADO_SCHEMA_ERROR_MESSAGE:
            raise
        raise RuntimeError(SOLO_LAVADO_SCHEMA_ERROR_MESSAGE) from exc
    except Exception as exc:
        raise RuntimeError(SOLO_LAVADO_SCHEMA_ERROR_MESSAGE) from exc

    _SCHEMA_ENSURED = True


def build_operacion_servicio_inicio(patente, wash_snapshot, usuario_inicio, fecha_hora_inicio):
    return {
        "patente": str(patente).upper(),
        "id_tipo_vehiculo_lavado": int(wash_snapshot["id_tipo_vehiculo_lavado"]),
        "tipo_vehiculo_lavado_snapshot": str(wash_snapshot["tipo_vehiculo_lavado_snapshot"]),
        "valor_lavado_snapshot": int(wash_snapshot["valor_lavado_snapshot"]),
        "fecha_hora_inicio": fecha_hora_inicio,
        "fecha_hora_fin": None,
        "usuario_inicio": usuario_inicio,
        "usuario_fin": None,
        "estado": ESTADO_ACTIVO,
        "id_ingreso_generado": None,
        "cobra_ahora": False,
    }


def transition_operacion_servicio(
    operacion,
    nuevo_estado,
    usuario_fin,
    fecha_hora_fin,
    id_ingreso_generado=None,
):
    estado_actual = operacion.get("estado")
    if estado_actual != ESTADO_ACTIVO:
        raise ValueError("OPERACION_SERVICIO_NOT_ACTIVE")

    if nuevo_estado not in _ESTADOS_FINALES:
        raise ValueError("OPERACION_SERVICIO_INVALID_TRANSITION")

    if nuevo_estado == ESTADO_CONVERTIDO_ESTADIA and id_ingreso_generado is None:
        raise ValueError("OPERACION_SERVICIO_REQUIRES_INGRESO_GENERADO")

    finalizada = dict(operacion)
    finalizada.update({
        "estado": nuevo_estado,
        "fecha_hora_fin": fecha_hora_fin,
        "usuario_fin": usuario_fin,
        "id_ingreso_generado": id_ingreso_generado,
        "cobra_ahora": nuevo_estado == ESTADO_FINALIZADO_COBRADO,
    })
    return finalizada


def calcular_duracion_minutos(inicio, fin):
    if not inicio or not fin or fin <= inicio:
        return 0
    return int((fin - inicio).total_seconds() // 60)


def iniciar_solo_lavado(patente, id_tipo_vehiculo_lavado, usuario_inicio):
    asegurar_schema_operaciones_servicio()
    ensure_wash_vehicle_type_table()
    patente_normalizada = requerir_patente_valida(patente)
    ahora = datetime.now()

    with db_cursor(dictionary=True, commit=True) as cursor:
        cursor.execute("""
            SELECT i.id_ingreso
            FROM ingresos i
            JOIN vehiculos v ON v.id_vehiculo = i.id_vehiculo
            WHERE UPPER(v.patente) = UPPER(%s)
              AND i.fecha_hora_salida IS NULL
            LIMIT 1
        """, (patente_normalizada,))
        if cursor.fetchone():
            return None

        cursor.execute("""
            SELECT id_tipo_vehiculo_lavado, nombre, valor_lavado, activo
            FROM tipos_vehiculo_lavado
            WHERE id_tipo_vehiculo_lavado = %s
            LIMIT 1
        """, (int(id_tipo_vehiculo_lavado),))
        tipo_lavado = cursor.fetchone()
        if not tipo_lavado:
            raise RuntimeError(SOLO_LAVADO_PRICE_CONFIG_MESSAGE)

        snapshot = build_wash_price_snapshot(tipo_lavado)
        operacion = build_operacion_servicio_inicio(
            patente_normalizada,
            snapshot,
            usuario_inicio,
            ahora,
        )

        cursor.execute("""
            INSERT INTO operaciones_servicio (
                patente, id_tipo_vehiculo_lavado, tipo_vehiculo_lavado_snapshot,
                valor_lavado_snapshot, fecha_hora_inicio, usuario_inicio, estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            operacion["patente"],
            operacion["id_tipo_vehiculo_lavado"],
            operacion["tipo_vehiculo_lavado_snapshot"],
            operacion["valor_lavado_snapshot"],
            operacion["fecha_hora_inicio"],
            operacion["usuario_inicio"],
            operacion["estado"],
        ))
        id_operacion = cursor.lastrowid

    operacion["id_operacion_servicio"] = id_operacion
    return operacion


def obtener_operacion_servicio_activa(id_operacion_servicio, cursor):
    cursor.execute("""
        SELECT id_operacion_servicio, patente, id_tipo_vehiculo_lavado,
               tipo_vehiculo_lavado_snapshot, valor_lavado_snapshot,
               fecha_hora_inicio, fecha_hora_fin, usuario_inicio,
               usuario_fin, estado, id_ingreso_generado
        FROM operaciones_servicio
        WHERE id_operacion_servicio = %s
          AND estado = 'ACTIVO'
        LIMIT 1
    """, (int(id_operacion_servicio),))
    return cursor.fetchone()


def finalizar_solo_lavado_cobrando(id_operacion_servicio, usuario_fin):
    asegurar_schema_operaciones_servicio()
    ahora = datetime.now()

    with db_cursor(dictionary=True, commit=True) as cursor:
        operacion = obtener_operacion_servicio_activa(id_operacion_servicio, cursor)
        if not operacion:
            return None

        finalizada = transition_operacion_servicio(
            operacion,
            ESTADO_FINALIZADO_COBRADO,
            usuario_fin,
            ahora,
        )
        cursor.execute("""
            UPDATE operaciones_servicio
            SET fecha_hora_fin = %s,
                usuario_fin = %s,
                estado = %s,
                duracion_minutos = TIMESTAMPDIFF(MINUTE, fecha_hora_inicio, %s)
            WHERE id_operacion_servicio = %s
        """, (
            finalizada["fecha_hora_fin"],
            finalizada["usuario_fin"],
            finalizada["estado"],
            finalizada["fecha_hora_fin"],
            int(id_operacion_servicio),
        ))

        finalizada["id_operacion_servicio"] = int(id_operacion_servicio)
        finalizada["duracion_minutos"] = calcular_duracion_minutos(
            finalizada.get("fecha_hora_inicio"),
            finalizada.get("fecha_hora_fin"),
        )
        if obtener_print_jobs_pc_activos(cursor):
            crear_print_job_solo_lavado(cursor, finalizada)

    return finalizada


def finalizar_solo_lavado_como_estadia(id_operacion_servicio, usuario_fin):
    asegurar_schema_operaciones_servicio()
    ahora = datetime.now()

    with db_cursor(dictionary=True, commit=True) as cursor:
        operacion = obtener_operacion_servicio_activa(id_operacion_servicio, cursor)
        if not operacion:
            return None

        cursor.execute(
            "SELECT id_vehiculo FROM vehiculos WHERE UPPER(patente) = UPPER(%s) LIMIT 1",
            (operacion["patente"],),
        )
        vehiculo = cursor.fetchone()
        if vehiculo:
            id_vehiculo = vehiculo["id_vehiculo"]
        else:
            cursor.execute(
                "INSERT INTO vehiculos (patente, tipo_cliente) VALUES (%s, 'ocasional')",
                (operacion["patente"],),
            )
            id_vehiculo = cursor.lastrowid

        cursor.execute("""
            INSERT INTO ingresos (id_vehiculo, fecha_hora_ingreso, en_espera)
            VALUES (%s, %s, 0)
        """, (id_vehiculo, ahora))
        id_ingreso_generado = cursor.lastrowid

        finalizada = transition_operacion_servicio(
            operacion,
            ESTADO_CONVERTIDO_ESTADIA,
            usuario_fin,
            ahora,
            id_ingreso_generado=id_ingreso_generado,
        )
        cursor.execute("""
            UPDATE operaciones_servicio
            SET fecha_hora_fin = %s,
                usuario_fin = %s,
                estado = %s,
                id_ingreso_generado = %s,
                duracion_minutos = TIMESTAMPDIFF(MINUTE, fecha_hora_inicio, %s)
            WHERE id_operacion_servicio = %s
        """, (
            finalizada["fecha_hora_fin"],
            finalizada["usuario_fin"],
            finalizada["estado"],
            finalizada["id_ingreso_generado"],
            finalizada["fecha_hora_fin"],
            int(id_operacion_servicio),
        ))

    finalizada["fecha_hora_ingreso"] = ahora
    finalizada["duracion_minutos"] = calcular_duracion_minutos(
        finalizada.get("fecha_hora_inicio"),
        finalizada.get("fecha_hora_fin"),
    )
    return finalizada


def obtener_operacion_convertida_por_ingreso(id_ingreso):
    try:
        asegurar_schema_operaciones_servicio()
        with db_cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT id_operacion_servicio, patente, tipo_vehiculo_lavado_snapshot,
                       valor_lavado_snapshot, fecha_hora_inicio, fecha_hora_fin,
                       usuario_inicio, usuario_fin, estado, id_ingreso_generado
                FROM operaciones_servicio
                WHERE id_ingreso_generado = %s
                  AND estado = 'CONVERTIDO_ESTADIA'
                LIMIT 1
            """, (int(id_ingreso),))
            return cursor.fetchone()
    except Exception as exc:
        print(f"[WARN] No se pudo consultar lavado convertido: {exc}")
        return None


def obtener_solo_lavados_activos():
    asegurar_schema_operaciones_servicio()
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id_operacion_servicio, patente, tipo_vehiculo_lavado_snapshot,
                   valor_lavado_snapshot, fecha_hora_inicio,
                   TIMESTAMPDIFF(MINUTE, fecha_hora_inicio, NOW()) AS minutos
            FROM operaciones_servicio
            WHERE estado = 'ACTIVO'
            ORDER BY fecha_hora_inicio DESC
        """)
        return cursor.fetchall()
