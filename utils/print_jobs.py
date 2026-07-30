"""Helpers para crear trabajos durables de impresion."""

import json
from datetime import date, datetime, time


def _json_safe(value):
    """Convierte valores de dominio anidados al formato del payload durable."""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def ingreso_idempotency_key(id_ingreso):
    return f"desktop-ingreso:{id_ingreso}:pc-pdf"


def salida_idempotency_key(id_ingreso, secuencia_reingreso=0):
    base = f"desktop-salida:{id_ingreso}:pc-pdf"
    if secuencia_reingreso:
        return f"{base}:reingreso:{secuencia_reingreso}"
    return base


def solo_lavado_idempotency_key(id_operacion_servicio):
    return f"desktop-solo-lavado:{id_operacion_servicio}:pc-pdf"


def crear_print_job_ingreso(cursor, id_ingreso, patente, fecha_hora_ingreso, cobro_noche=None):
    """Inserta el ticket de ingreso en la transaccion del ingreso."""
    hora_ingreso = fecha_hora_ingreso.isoformat(timespec="seconds")
    payload = {
        "kind": "TICKET_INGRESO",
        "id_ingreso": id_ingreso,
        "patente": patente,
        "hora_ingreso": hora_ingreso,
        "usuario": {
            "id_usuario": None,
            "usuario": None,
            "rol": None,
        },
        "tarifa": {"monto_preliminar": 0},
        "meta": {"server_time": hora_ingreso, "version": 1},
    }
    if cobro_noche:
        payload["noches"] = cobro_noche
    cursor.execute(
        """
        INSERT INTO print_jobs
            (tipo, destino, id_ingreso, patente, payload_json, estado, idempotency_key)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            "TICKET_INGRESO",
            "PC_PDF",
            id_ingreso,
            patente,
            json.dumps(payload, ensure_ascii=False),
            "PENDIENTE",
            ingreso_idempotency_key(id_ingreso),
        ),
    )


def crear_print_job_salida(
    cursor,
    id_ingreso,
    patente,
    fecha_hora_ingreso,
    fecha_hora_salida,
    minutos,
    total_a_cobrar,
    detalle_cobro,
    tarifa,
    total_lavados,
    usuario,
    modo_cobro=None,
    subida_aplicada=False,
    monto_extra=0,
    secciones=None,
    idempotency_key=None,
    noches_prepagadas=None,
):
    """Inserta el ticket de salida en la transaccion del cierre."""
    hora_ingreso = fecha_hora_ingreso.isoformat(timespec="seconds")
    hora_salida = fecha_hora_salida.isoformat(timespec="seconds")
    payload = {
        "kind": "TICKET_SALIDA",
        "id_ingreso": id_ingreso,
        "patente": patente,
        "hora_ingreso": hora_ingreso,
        "hora_salida": hora_salida,
        "minutos_cobrados": minutos,
        "monto_final": total_a_cobrar,
        "detalle": {
            "texto": detalle_cobro,
            "monto_estacionamiento": tarifa,
            "total_lavados": total_lavados,
            "modo_cobro": modo_cobro,
            "subida_aplicada": subida_aplicada,
            "monto_extra": monto_extra,
            "secciones": _json_safe(secciones),
        },
        "usuario": {
            "id_usuario": None,
            "usuario": usuario,
            "rol": None,
        },
        "meta": {"server_time": hora_salida, "version": 1},
    }
    if noches_prepagadas:
        payload["noches_prepagadas"] = noches_prepagadas
    cursor.execute(
        """
        INSERT INTO print_jobs
            (tipo, destino, id_ingreso, patente, payload_json, estado, idempotency_key)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            "TICKET_SALIDA",
            "PC_PDF",
            id_ingreso,
            patente,
            json.dumps(payload, ensure_ascii=False),
            "PENDIENTE",
            idempotency_key or salida_idempotency_key(id_ingreso),
        ),
    )


def crear_print_job_solo_lavado(cursor, operacion):
    """Inserta el recibo de solo lavado en la transaccion de su cobro."""
    id_operacion = int(operacion["id_operacion_servicio"])
    hora_inicio = operacion["fecha_hora_inicio"].isoformat(timespec="seconds")
    hora_fin = operacion["fecha_hora_fin"].isoformat(timespec="seconds")
    monto_final = int(operacion["valor_lavado_snapshot"])
    servicio = str(operacion.get("tipo_vehiculo_lavado_snapshot") or "Lavado")
    payload = {
        "kind": "TICKET_SOLO_LAVADO",
        "id_operacion_servicio": id_operacion,
        "patente": operacion["patente"],
        "servicio": servicio,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "minutos": int(operacion.get("duracion_minutos") or 0),
        "monto_final": monto_final,
        "total": monto_final,
        "detalle_texto": f"Lavado {servicio}",
        "meta": {"server_time": hora_fin, "version": 1},
    }
    cursor.execute(
        """
        INSERT INTO print_jobs
            (tipo, destino, id_ingreso, patente, payload_json, estado, idempotency_key)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            "TICKET_SOLO_LAVADO",
            "PC_PDF",
            None,
            operacion["patente"],
            json.dumps(payload, ensure_ascii=False),
            "PENDIENTE",
            solo_lavado_idempotency_key(id_operacion),
        ),
    )
