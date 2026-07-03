import mysql.connector

from controllers.config_controller import LAVADO_CATEGORIAS
from utils.db import db_cursor


PARKING_TARIFF_FIELDS = {"tarifa_hora", "tarifa_minima", "valor_minuto", "modo_cobro"}
WASH_VEHICLE_TYPE_TABLES = ("tipos_vehiculo_lavado", "tipos_vehiculos_lavado")
_WASH_TYPES_ENSURED = False
_DUPLICATE_SCHEMA_ERROR_CODES = {1060, 1061, 1062}

SOLO_LAVADO_PRICE_CONFIG_MESSAGE = (
    "Solo lavado no tiene precios activos configurados. "
    "Configurá o activá un precio/tipo de lavado en Configuración para Solo lavado."
)


def _execute_schema(cursor, statement, params=None):
    try:
        cursor.execute(statement, params)
    except mysql.connector.Error as exc:
        if getattr(exc, "errno", None) in _DUPLICATE_SCHEMA_ERROR_CODES:
            return
        raise


def _looks_like_missing_wash_table(exc):
    message = str(exc).lower()
    return any(table in message for table in WASH_VEHICLE_TYPE_TABLES) and (
        "doesn't exist" in message or "does not exist" in message or "no such table" in message
    )


def ensure_wash_vehicle_type_table():
    """Ensure canonical solo-lavado vehicle type prices exist for deployed DBs."""
    global _WASH_TYPES_ENSURED
    if _WASH_TYPES_ENSURED:
        return

    with db_cursor(commit=True) as cursor:
        _execute_schema(cursor, """
            CREATE TABLE IF NOT EXISTS tipos_vehiculo_lavado (
                id_tipo_vehiculo_lavado INT AUTO_INCREMENT PRIMARY KEY,
                codigo VARCHAR(50) NOT NULL UNIQUE,
                nombre VARCHAR(80) NOT NULL,
                valor_lavado INT NOT NULL,
                activo TINYINT(1) NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        _copy_plural_wash_types_if_present(cursor)
        _seed_wash_types_from_legacy_config(cursor)

    _WASH_TYPES_ENSURED = True


def _copy_plural_wash_types_if_present(cursor):
    try:
        cursor.execute("""
            INSERT INTO tipos_vehiculo_lavado (codigo, nombre, valor_lavado, activo)
            SELECT codigo, nombre, valor_lavado, activo
            FROM tipos_vehiculos_lavado
            ON DUPLICATE KEY UPDATE
                nombre = VALUES(nombre),
                valor_lavado = VALUES(valor_lavado),
                activo = VALUES(activo)
        """)
    except Exception as exc:
        if not _looks_like_missing_wash_table(exc):
            raise


def _seed_wash_types_from_legacy_config(cursor):
    cursor.execute("SELECT clave, valor FROM configuracion WHERE clave LIKE 'lavado_%'")
    configured = {row[0] if not isinstance(row, dict) else row["clave"]: row[1] if not isinstance(row, dict) else row["valor"] for row in cursor.fetchall()}
    for clave, label, default in LAVADO_CATEGORIAS:
        amount = _positive_int_or_none(configured.get(clave, default))
        if amount is None:
            continue
        cursor.execute("""
            INSERT INTO tipos_vehiculo_lavado (codigo, nombre, valor_lavado, activo)
            VALUES (%s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE
                nombre = VALUES(nombre),
                valor_lavado = VALUES(valor_lavado),
                activo = 1
        """, (clave, label, amount))


def _positive_int_or_none(value):
    try:
        amount = int(float(value))
    except (TypeError, ValueError):
        return None
    return amount if amount > 0 else None


def build_wash_vehicle_type_payload(payload):
    if PARKING_TARIFF_FIELDS.intersection(payload.keys()):
        raise ValueError("PARKING_TARIFF_FIELDS_NOT_ALLOWED")

    return {
        "codigo": str(payload["codigo"]).strip(),
        "nombre": str(payload["nombre"]).strip(),
        "valor_lavado": int(payload["valor_lavado"]),
        "activo": 1 if payload.get("activo", True) else 0,
    }


def build_wash_price_snapshot(wash_vehicle_type):
    if not int(wash_vehicle_type.get("activo", 0)):
        raise ValueError("INACTIVE_WASH_VEHICLE_TYPE")

    return {
        "id_tipo_vehiculo_lavado": int(wash_vehicle_type["id_tipo_vehiculo_lavado"]),
        "tipo_vehiculo_lavado_snapshot": str(wash_vehicle_type["nombre"]),
        "valor_lavado_snapshot": int(wash_vehicle_type["valor_lavado"]),
    }


def resolve_wash_type_delete_action(reference_count):
    return "deactivate" if int(reference_count or 0) > 0 else "delete"


def list_wash_vehicle_types():
    ensure_wash_vehicle_type_table()
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id_tipo_vehiculo_lavado, codigo, nombre, valor_lavado, activo
            FROM tipos_vehiculo_lavado
            ORDER BY nombre ASC
        """)
        rows = cursor.fetchall()
    items = [dict(row) for row in rows]
    if not items:
        raise RuntimeError(SOLO_LAVADO_PRICE_CONFIG_MESSAGE)
    return items


def create_wash_vehicle_type(payload):
    ensure_wash_vehicle_type_table()
    data = build_wash_vehicle_type_payload(payload)
    with db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO tipos_vehiculo_lavado (codigo, nombre, valor_lavado, activo)
            VALUES (%s, %s, %s, %s)
        """, (data["codigo"], data["nombre"], data["valor_lavado"], data["activo"]))
    return True


def update_wash_vehicle_type(id_tipo_vehiculo_lavado, payload):
    ensure_wash_vehicle_type_table()
    data = build_wash_vehicle_type_payload(payload)
    with db_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE tipos_vehiculo_lavado
            SET codigo = %s, nombre = %s, valor_lavado = %s, activo = %s
            WHERE id_tipo_vehiculo_lavado = %s
        """, (
            data["codigo"],
            data["nombre"],
            data["valor_lavado"],
            data["activo"],
            int(id_tipo_vehiculo_lavado),
        ))
        if cursor.rowcount != 1:
            raise LookupError("WASH_VEHICLE_TYPE_NOT_FOUND")
    return True


def delete_wash_vehicle_type(id_tipo_vehiculo_lavado):
    ensure_wash_vehicle_type_table()
    with db_cursor(commit=True) as cursor:
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM lavados WHERE id_tipo_vehiculo_lavado = %s) +
                (SELECT COUNT(*) FROM operaciones_servicio WHERE id_tipo_vehiculo_lavado = %s)
                AS total
        """, (int(id_tipo_vehiculo_lavado), int(id_tipo_vehiculo_lavado)))
        row = cursor.fetchone() or {"total": 0}
        action = resolve_wash_type_delete_action(row.get("total", 0))

        if action == "deactivate":
            cursor.execute("""
                UPDATE tipos_vehiculo_lavado
                SET activo = 0
                WHERE id_tipo_vehiculo_lavado = %s
            """, (int(id_tipo_vehiculo_lavado),))
            action = "deactivated"
        else:
            cursor.execute("""
                DELETE FROM tipos_vehiculo_lavado
                WHERE id_tipo_vehiculo_lavado = %s
            """, (int(id_tipo_vehiculo_lavado),))
            action = "deleted"

        if cursor.rowcount != 1:
            raise LookupError("WASH_VEHICLE_TYPE_NOT_FOUND")
    return action
