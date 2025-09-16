"""
Controlador para la gestión de asistencias de usuarios.

Incluye funciones para consultar asistencias registradas en el sistema.
"""

from utils.db import get_connection
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
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

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

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados