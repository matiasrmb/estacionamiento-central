"""
Controlador del resumen diario del sistema.

Obtiene estadísticas simples para el panel principal (dashboard) del sistema.
"""

from utils.db import db_cursor
from utils.slowlog import slow_operation
from controllers.registro_controller import obtener_resumen_caja_actual

@slow_operation("dashboard_refresh")
def obtener_resumen_diario():
    """
    Obtiene el resumen desde el último cierre diario hasta ahora,
    incluyendo:
    - Cantidad total de ingresos desde el último cierre
    - Vehículos actualmente estacionados
    - Total recaudado desde el último cierre
    """
    with db_cursor(dictionary=True) as cursor:
        # Obtener fecha del último cierre
        cursor.execute("SELECT MAX(fecha_cierre) AS ultima_cierre FROM cierres_diarios")
        row = cursor.fetchone()
        fecha_inicio = row["ultima_cierre"] if row and row["ultima_cierre"] else "1970-01-01 00:00:00"

        # Total de ingresos desde último cierre
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM ingresos
            WHERE fecha_hora_ingreso > %s AND fecha_hora_ingreso <= NOW()
              AND NOT EXISTS (
                  SELECT 1 FROM ingresos_eliminados ie
                  WHERE ie.id_ingreso_original = ingresos.id_ingreso
              )
        """, (fecha_inicio,))
        total_ingresos = cursor.fetchone()["total"]

        # Vehículos estacionados actualmente (sin salida)
        cursor.execute("""
            SELECT COUNT(*) AS estacionados
            FROM ingresos
            WHERE fecha_hora_ingreso > %s
              AND fecha_hora_salida IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM ingresos_eliminados ie
                  WHERE ie.id_ingreso_original = ingresos.id_ingreso
              )
        """, (fecha_inicio,))
        total_estacionados = cursor.fetchone()["estacionados"]

    # Reuse the daily-close sources so dashboard cards cannot drift from cashbox.
    caja = obtener_resumen_caja_actual()
    recaudado = (
        caja["total_recaudado"]
        + caja["total_lavados_solos_monto"]
        + caja["total_mensualidades_monto"]
        + caja["total_noches_monto"]
    )

    return {
        "total_ingresos": total_ingresos,
        "estacionados": total_estacionados,
        "recaudado": recaudado,
        "total_general": caja["total_general"],
        "total_neto": caja["total_neto"],
    }


@slow_operation("dashboard_refresh")
def obtener_resumen_banos():
    """
    Obtiene estadísticas de usos de baños desde el último cierre diario hasta ahora.
    """
    with db_cursor(dictionary=True) as cursor:
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

    return {
        "cantidad": row["cantidad"] or 0,
        "total": row["total"] or 0
    }
