"""
Controlador para la generación de cierres diarios.

Incluye lógica para consolidar ingresos y generar reportes en PDF.
"""

from utils.db import get_connection
from utils.pdf import generar_pdf_cierre
from datetime import datetime, timedelta

def realizar_cierre_diario(usuario):
    """
    Realiza el cierre diario de ingresos y genera un resumen en PDF.

    Args:
        usuario (str): Usuario que ejecuta el cierre.

    Returns:
        tuple: (bool, str) indicando si el cierre fue exitoso y un mensaje informativo.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_ingreso, fecha_hora_ingreso, fecha_hora_salida, tarifa_aplicada
        FROM ingresos
        WHERE fecha_hora_salida IS NOT NULL AND cerrado = FALSE
    """)
    registros = cursor.fetchall()

    if not registros:
        cursor.close()
        conn.close()
        return False, "No hay registros para cerrar hoy."

    fecha_inicio = min([r["fecha_hora_ingreso"] for r in registros])
    fecha_cierre = datetime.now()
    total_recaudado = sum([r["tarifa_aplicada"] for r in registros if r["tarifa_aplicada"] is not None])
    total_ingresos = len(registros)
    total_salidas = total_ingresos  # Ingreso con salida registrada

    # Obtener información de baños durante el mismo rango de tiempo
    cursor.execute("""
        SELECT COUNT(*) AS cantidad, SUM(monto) AS total
        FROM usos_bano
        WHERE fecha_hora BETWEEN %s AND %s
    """, (fecha_inicio, fecha_cierre))
    banos = cursor.fetchone()
    total_banos = banos["cantidad"] or 0
    total_banos_monto = banos["total"] or 0

    # Total combinado
    total_general = total_recaudado + total_banos_monto

    # Insertar el resumen en la tabla cierres
    cursor.execute("""
        INSERT INTO cierres_diarios (
            fecha_inicio, fecha_cierre, total_recaudado,
            total_ingresos, total_salidas, usuario
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (fecha_inicio, fecha_cierre, total_recaudado,
          total_ingresos, total_salidas, usuario))

    # Marcar ingresos como cerrados
    ids = [r["id_ingreso"] for r in registros]
    formato = ','.join(['%s'] * len(ids))
    cursor.execute(f"""
        UPDATE ingresos SET cerrado = TRUE
        WHERE id_ingreso IN ({formato})
    """, ids)

    conn.commit()

    datos_pdf = {
        "Fecha de inicio": fecha_inicio.strftime("%Y-%m-%d %H:%M"),
        "Fecha de cierre": fecha_cierre.strftime("%Y-%m-%d %H:%M"),
        "Total recaudado vehículos": f"${total_recaudado}",
        "Total baños registrados": total_banos,
        "Total recaudado baños": f"${total_banos_monto}",
        "Total ingresos": total_ingresos,
        "Total salidas": total_salidas,
        "Total general del día": f"${total_general}",
        "Registrado por": usuario
    }
    generar_pdf_cierre("diario", datos_pdf)

    cursor.close()
    conn.close()
    return True, f"Cierre realizado con éxito. Total recaudado: ${total_general}"

