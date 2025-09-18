"""
Controlador del resumen diario del sistema.

Obtiene estadísticas simples para el panel principal (dashboard) del sistema.
"""

from utils.db import get_connection

def obtener_resumen_diario():
    """
    Obtiene el resumen diario del sistema, incluyendo:
    - Cantidad total de ingresos de hoy
    - Vehículos actualmente estacionados
    - Total recaudado hoy

    Returns:
        dict: Resumen con claves 'total_ingresos', 'estacionados' y 'recaudado'.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS total_hoy
        FROM ingresos
        WHERE DATE(fecha_hora_ingreso) = CURDATE()
    """)
    total_ingresos = cursor.fetchone()["total_hoy"]

    cursor.execute("""
        SELECT COUNT(*) AS estacionados
        FROM ingresos
        WHERE fecha_hora_salida IS NULL
    """)
    total_estacionados = cursor.fetchone()["estacionados"]

    cursor.execute("""
        SELECT SUM(tarifa_aplicada) AS recaudado
        FROM ingresos
        WHERE DATE(fecha_hora_salida) = CURDATE()
          AND cerrado = FALSE
    """)
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
    Obtiene estadísticas de usos de baños del día actual.

    Returns:
        dict: Contiene cantidad de usos y total recaudado.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS cantidad, SUM(monto) AS total
        FROM usos_bano
        WHERE DATE(fecha_hora) = CURDATE()
    """)
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "cantidad": row["cantidad"] or 0,
        "total": row["total"] or 0
    }
