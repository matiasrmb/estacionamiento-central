"""
Controlador para la gestión de clientes mensuales del sistema de estacionamiento.
"""

from calendar import monthrange
from datetime import datetime

import mysql.connector

from utils.db import db_cursor


_SCHEMA_MENSUALES_ASEGURADO = False
_DUPLICATE_SCHEMA_ERROR_CODES = {1060, 1061}


def _ejecutar_schema(cursor, sentencia):
    try:
        cursor.execute(sentencia)
    except mysql.connector.Error as exc:
        if getattr(exc, "errno", None) not in _DUPLICATE_SCHEMA_ERROR_CODES:
            raise


def asegurar_schema_mensuales():
    """Agrega las estructuras de mensualidades en instalaciones existentes."""
    global _SCHEMA_MENSUALES_ASEGURADO
    if _SCHEMA_MENSUALES_ASEGURADO:
        return

    with db_cursor(commit=True) as cursor:
        _ejecutar_schema(
            cursor,
            "ALTER TABLE vehiculos ADD COLUMN dia_vencimiento TINYINT UNSIGNED NOT NULL DEFAULT 1",
        )
        _ejecutar_schema(cursor, "ALTER TABLE vehiculos ADD COLUMN telefono VARCHAR(30) NULL")
        _ejecutar_schema(cursor, "ALTER TABLE cierres_diarios ADD COLUMN total_mensualidades INT NOT NULL DEFAULT 0")
        _ejecutar_schema(cursor, "ALTER TABLE cierres_diarios ADD COLUMN total_mensualidades_monto INT NOT NULL DEFAULT 0")
        _ejecutar_schema(cursor, """
            CREATE TABLE IF NOT EXISTS pagos_mensuales (
                id_pago_mensual INT AUTO_INCREMENT PRIMARY KEY,
                id_vehiculo INT NOT NULL,
                periodo DATE NOT NULL,
                fecha_pago DATETIME NOT NULL,
                monto_snapshot INT NOT NULL,
                dia_vencimiento_snapshot TINYINT UNSIGNED NOT NULL,
                usuario VARCHAR(50) NOT NULL,
                metodo_pago VARCHAR(50) NULL,
                observacion VARCHAR(500) NULL,
                id_cierre INT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_pagos_mensuales_vehiculo_periodo (id_vehiculo, periodo),
                INDEX idx_pagos_mensuales_cierre (id_cierre),
                INDEX idx_pagos_mensuales_fecha_pago (fecha_pago),
                FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo),
                FOREIGN KEY (id_cierre) REFERENCES cierres_diarios(id_cierre)
            )
        """)

    _SCHEMA_MENSUALES_ASEGURADO = True


def fecha_vencimiento_efectiva(periodo, dia_vencimiento):
    """Devuelve el vencimiento ajustado al último día real del mes."""
    return periodo.replace(day=min(int(dia_vencimiento), monthrange(periodo.year, periodo.month)[1]))


def estado_pago_mensual(periodo, dia_vencimiento, pago_registrado, ahora=None):
    if pago_registrado:
        return "pagado"
    ahora = ahora or datetime.now()
    if ahora.date() > fecha_vencimiento_efectiva(periodo, dia_vencimiento).date():
        return "vencido"
    return "pendiente"


def _periodo_actual(ahora=None):
    ahora = ahora or datetime.now()
    return ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def obtener_mensuales(ahora=None):
    """
    Obtiene una lista de vehículos registrados como clientes mensuales activos.

    Returns:
        list: Lista de diccionarios con 'id_vehiculo', 'patente' y 'tarifa_mensual'.
    """
    asegurar_schema_mensuales()
    periodo = _periodo_actual(ahora)
    query = """
        SELECT v.id_vehiculo, v.patente, v.tarifa_mensual, v.dia_vencimiento, v.telefono,
               %s AS periodo, p.id_pago_mensual, p.fecha_pago, p.monto_snapshot,
               p.metodo_pago, p.observacion,
               CASE
                   WHEN p.id_pago_mensual IS NOT NULL THEN 'pagado'
                   WHEN DAY(%s) > LEAST(v.dia_vencimiento, DAY(LAST_DAY(%s))) THEN 'vencido'
                   ELSE 'pendiente'
               END AS estado_pago
        FROM vehiculos v
        LEFT JOIN pagos_mensuales p ON p.id_vehiculo = v.id_vehiculo AND p.periodo = %s
        WHERE v.tipo_cliente = 'mensual' AND v.activo = 1
        ORDER BY v.patente
    """

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, (periodo.date(), ahora or datetime.now(), periodo.date(), periodo.date()))
        resultados = cursor.fetchall()

    return resultados

def agregar_mensual(patente, tarifa_mensual=None, dia_vencimiento=None, telefono=None):
    """
    Agrega o actualiza una patente como cliente mensual.

    Args:
        patente (str): Patente del vehículo.
        tarifa_mensual (int | None): Valor mensual opcional.
        dia_vencimiento (int | None): Día de vencimiento opcional.
        telefono (str | None): Teléfono de contacto opcional.

    Returns:
        bool: True si la operación fue exitosa.
    """
    with db_cursor(commit=True) as cursor:
        # Verificar si ya existe como mensual
        cursor.execute("SELECT * FROM vehiculos WHERE patente = %s", (patente,))
        existente = cursor.fetchone()

        if existente:
            if tarifa_mensual is None and dia_vencimiento is None and telefono is None:
                cursor.execute(
                    "UPDATE vehiculos SET tipo_cliente = 'mensual', activo = 1 WHERE patente = %s",
                    (patente,)
                )
            else:
                cursor.execute(
                    """UPDATE vehiculos
                       SET tipo_cliente = 'mensual', activo = 1, tarifa_mensual = %s,
                           dia_vencimiento = %s, telefono = %s
                       WHERE patente = %s""",
                    (tarifa_mensual, dia_vencimiento, telefono, patente),
                )
        else:
            cursor.execute(
                """INSERT INTO vehiculos
                   (patente, tipo_cliente, activo, tarifa_mensual, dia_vencimiento, telefono)
                   VALUES (%s, 'mensual', 1, %s, %s, %s)""",
                (patente, tarifa_mensual, dia_vencimiento or 1, telefono),
            )

    return True

def eliminar_mensual(id_vehiculo):
    """
    Desactiva a un cliente mensual (no elimina el registro).

    Args:
        id_vehiculo (int): ID del vehículo.

    Returns:
        bool: True si la operación fue exitosa.
    """
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE vehiculos SET activo = 0 WHERE id_vehiculo = %s",
            (id_vehiculo,)
        )

    return True

def actualizar_tarifa(id_vehiculo, nueva_tarifa, dia_vencimiento=None, telefono=None):
    """
    Modifica la tarifa mensual asociada a un cliente.

    Args:
        id_vehiculo (int): ID del vehículo.
        nueva_tarifa (int): Nuevo valor de la tarifa mensual.
        dia_vencimiento (int | None): Nuevo día de vencimiento.
        telefono (str | None): Nuevo teléfono de contacto.

    Returns:
        bool: True si la operación fue exitosa.
    """
    with db_cursor(commit=True) as cursor:
        if dia_vencimiento is None and telefono is None:
            cursor.execute(
                "UPDATE vehiculos SET tarifa_mensual = %s WHERE id_vehiculo = %s",
                (nueva_tarifa, id_vehiculo)
            )
        else:
            cursor.execute(
                """UPDATE vehiculos
                   SET tarifa_mensual = %s, dia_vencimiento = %s, telefono = %s
                   WHERE id_vehiculo = %s""",
                (nueva_tarifa, dia_vencimiento, telefono, id_vehiculo)
            )

    return True


def registrar_pago_mensual(id_vehiculo, usuario, metodo_pago=None, observacion=None, ahora=None):
    """Registra un único cobro mensual para el período actual."""
    asegurar_schema_mensuales()
    ahora = ahora or datetime.now()
    periodo = _periodo_actual(ahora).date()
    with db_cursor(dictionary=True, commit=True) as cursor:
        cursor.execute("""
            SELECT id_vehiculo, tipo_cliente, activo, tarifa_mensual, dia_vencimiento
            FROM vehiculos
            WHERE id_vehiculo = %s
            FOR UPDATE
        """, (id_vehiculo,))
        vehiculo = cursor.fetchone()
        if not vehiculo or vehiculo.get("tipo_cliente") != "mensual" or not vehiculo.get("activo"):
            return False, "El vehículo no es un cliente mensual activo."

        monto = int(vehiculo.get("tarifa_mensual") or 0)
        dia_vencimiento = int(vehiculo.get("dia_vencimiento") or 0)
        if monto <= 0:
            return False, "La tarifa mensual debe ser mayor que cero."
        if not 1 <= dia_vencimiento <= 31:
            return False, "El día de vencimiento debe estar entre 1 y 31."

        cursor.execute(
            "SELECT id_pago_mensual FROM pagos_mensuales WHERE id_vehiculo = %s AND periodo = %s FOR UPDATE",
            (id_vehiculo, periodo),
        )
        if cursor.fetchone():
            return False, "El período actual ya fue pagado."

        try:
            cursor.execute("""
                INSERT INTO pagos_mensuales (
                    id_vehiculo, periodo, fecha_pago, monto_snapshot,
                    dia_vencimiento_snapshot, usuario, metodo_pago, observacion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (id_vehiculo, periodo, ahora, monto, dia_vencimiento, usuario, metodo_pago, observacion))
        except mysql.connector.Error as exc:
            if getattr(exc, "errno", None) == 1062:
                return False, "El período actual ya fue pagado."
            raise

    return True, "Pago mensual registrado."
