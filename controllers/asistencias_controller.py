"""
Controlador para la gestión de asistencias de usuarios.

Incluye funciones para consultar asistencias registradas en el sistema.
"""

from utils.db import db_cursor
from datetime import datetime, time

def obtener_asistencias(usuario=None, fecha_inicio=None, fecha_fin=None):
    """
    Obtiene una lista de asistencias filtradas por usuario y rango de fechas.

    Args:
        usuario (str, opcional): Nombre de usuario a filtrar. Si es None, se obtienen todas las asistencias.
        fecha_inicio (datetime.date, opcional): Fecha inicial para el filtro.
        fecha_fin (datetime.date, opcional): Fecha final para el filtro.

    Returns:
        list[dict]: Lista de asistencias, cada una como diccionario con campos como usuario, hora_inicio, hora_salida, etc.
    """
    query = """
        SELECT usuario, hora_inicio, hora_salida, cantidad_movimientos, total_recaudado
        FROM asistencias
        WHERE 1=1
    """
    params = []

    if usuario:
        query += " AND usuario = %s"
        params.append(usuario)

    if fecha_inicio and fecha_fin:
        inicio = datetime.combine(fecha_inicio, time.min)  # 00:00:00
        fin = datetime.combine(fecha_fin, time.max)        # 23:59:59.999999
        query += " AND hora_inicio BETWEEN %s AND %s"
        params.extend([inicio, fin])

    query += " ORDER BY hora_inicio DESC"

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, params)
        resultados = cursor.fetchall()

        ahora = datetime.now()
        for fila in resultados:
            if fila["hora_salida"] is None:
                cantidad, total = _calcular_totales_turno(
                    cursor,
                    fila["usuario"],
                    fila["hora_inicio"],
                    ahora,
                )
                fila["cantidad_movimientos"] = cantidad
                fila["total_recaudado"] = total

    return resultados


def _calcular_totales_turno(cursor, usuario, hora_inicio, hora_fin):
    cursor.execute("""
        SELECT COUNT(*) AS cantidad, COALESCE(SUM(tarifa_aplicada), 0) AS total
        FROM ingresos
        WHERE usuario = %s AND fecha_hora_salida BETWEEN %s AND %s
    """, (usuario, hora_inicio, hora_fin))
    salidas = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) AS cantidad, COALESCE(SUM(monto), 0) AS total
        FROM usos_bano
        WHERE usuario = %s AND fecha_hora BETWEEN %s AND %s
    """, (usuario, hora_inicio, hora_fin))
    banos = cursor.fetchone()

    salidas = salidas or {"cantidad": 0, "total": 0}
    banos = banos or {"cantidad": 0, "total": 0}
    cantidad = (salidas["cantidad"] or 0) + (banos["cantidad"] or 0)
    total = (salidas["total"] or 0) + (banos["total"] or 0)
    return cantidad, total
