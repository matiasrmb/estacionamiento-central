from utils.db import get_connection

def obtener_resumen_diario():
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
    """)
    recaudado = cursor.fetchone()["recaudado"] or 0

    cursor.close()
    conn.close()

    return {
        "total_ingresos": total_ingresos,
        "estacionados": total_estacionados,
        "recaudado": recaudado
    }
