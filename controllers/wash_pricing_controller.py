from utils.db import db_cursor


PARKING_TARIFF_FIELDS = {"tarifa_hora", "tarifa_minima", "valor_minuto", "modo_cobro"}


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
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id_tipo_vehiculo_lavado, codigo, nombre, valor_lavado, activo
            FROM tipos_vehiculo_lavado
            ORDER BY nombre ASC
        """)
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def create_wash_vehicle_type(payload):
    data = build_wash_vehicle_type_payload(payload)
    with db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO tipos_vehiculo_lavado (codigo, nombre, valor_lavado, activo)
            VALUES (%s, %s, %s, %s)
        """, (data["codigo"], data["nombre"], data["valor_lavado"], data["activo"]))
    return True


def update_wash_vehicle_type(id_tipo_vehiculo_lavado, payload):
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
