from datetime import datetime

from controllers.wash_pricing_controller import build_wash_price_snapshot
from utils.db import db_cursor
from utils.ticket import generar_ticket_solo_lavado


ESTADO_ACTIVO = "ACTIVO"
ESTADO_FINALIZADO_COBRADO = "FINALIZADO_COBRADO"
ESTADO_CONVERTIDO_ESTADIA = "CONVERTIDO_ESTADIA"

_ESTADOS_FINALES = {ESTADO_FINALIZADO_COBRADO, ESTADO_CONVERTIDO_ESTADIA}


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
    patente_normalizada = str(patente).strip().upper()
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
            return None

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

    finalizada["duracion_minutos"] = calcular_duracion_minutos(
        finalizada.get("fecha_hora_inicio"),
        finalizada.get("fecha_hora_fin"),
    )
    generar_ticket_solo_lavado(finalizada)
    return finalizada


def finalizar_solo_lavado_como_estadia(id_operacion_servicio, usuario_fin):
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
    try:
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
    except Exception as exc:
        print(f"[WARN] No se pudieron consultar solo lavados activos: {exc}")
        return []
