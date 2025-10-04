"""
Controlador del resumen diario del sistema.

Obtiene estadísticas simples para el panel principal (dashboard) del sistema.
"""

from utils.db import get_connection

def obtener_resumen_diario():
    """
    Obtiene el resumen desde el último cierre diario hasta ahora,
    incluyendo:
    - Cantidad total de ingresos desde el último cierre
    - Vehículos actualmente estacionados
    - Total recaudado desde el último cierre
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener fecha del último cierre
    cursor.execute("SELECT MAX(fecha_cierre) AS ultima_cierre FROM cierres_diarios")
    row = cursor.fetchone()
    fecha_inicio = row["ultima_cierre"] if row and row["ultima_cierre"] else "1970-01-01 00:00:00"

    # Total de ingresos desde último cierre
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM ingresos
        WHERE fecha_hora_ingreso > %s AND fecha_hora_ingreso <= NOW()
    """, (fecha_inicio,))
    total_ingresos = cursor.fetchone()["total"]

    # Vehículos estacionados actualmente (sin salida)
    cursor.execute("""
        SELECT COUNT(*) AS estacionados
        FROM ingresos
        WHERE fecha_hora_ingreso > %s
          AND fecha_hora_salida IS NULL
    """, (fecha_inicio,))
    total_estacionados = cursor.fetchone()["estacionados"]

    # Total recaudado desde último cierre
    cursor.execute("""
        SELECT SUM(tarifa_aplicada) AS recaudado
        FROM ingresos
        WHERE fecha_hora_salida > %s
          AND fecha_hora_salida <= NOW()
          AND cerrado = FALSE
    """, (fecha_inicio,))
    recaudado = cursor.fetchone()["recaudado"] or 0

    cursor.close()
    conn.close()

    return {
        "total_ingresos": total_ingresos,
        "estacionados": total_estacionados,
        "recaudado": recaudado
    }


def obtener_resumen_banos():
    """
    Obtiene estadísticas de usos de baños desde el último cierre diario hasta ahora.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener fecha del último cierre
    cursor.execute("SELECT MAX(fecha_cierre) AS ultima_cierre FROM cierres_diarios")
    row = cursor.fetchone()
    fecha_inicio = row["ultima_cierre"] if row and row["ultima_cierre"] else "1970-01-01 00:00:00"

    cursor.execute("""
        SELECT COUNT(*) AS cantidad, SUM(monto) AS total
        FROM usos_bano
        WHERE fecha_hora > %s AND fecha_hora <= NOW()
    """, (fecha_inicio,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "cantidad": row["cantidad"] or 0,
        "total": row["total"] or 0
    }
