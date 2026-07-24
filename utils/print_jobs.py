"""Helpers para crear trabajos durables de impresion."""

import json


def ingreso_idempotency_key(id_ingreso):
    return f"desktop-ingreso:{id_ingreso}:pc-pdf"


def salida_idempotency_key(id_ingreso):
    return f"desktop-salida:{id_ingreso}:pc-pdf"


def crear_print_job_ingreso(cursor, id_ingreso, patente, fecha_hora_ingreso):
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
        },
        "usuario": {
            "id_usuario": None,
            "usuario": usuario,
            "rol": None,
        },
        "meta": {"server_time": hora_salida, "version": 1},
    }
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
            salida_idempotency_key(id_ingreso),
        ),
    )
