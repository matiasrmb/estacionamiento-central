from utils.db import get_connection
from utils.pdf import generar_pdf_cierre
from datetime import datetime

def realizar_cierre_diario(usuario):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener todos los ingresos cerrables (salidas completadas y no cerrados aún)
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
    total_salidas = total_ingresos  # En este sistema, ingreso = salida registrada

    # Insertar el resumen en la tabla de cierres
    cursor.execute("""
        INSERT INTO cierres_diarios (
            fecha_inicio, fecha_cierre, total_recaudado,
            total_ingresos, total_salidas, usuario
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (fecha_inicio, fecha_cierre, total_recaudado,
          total_ingresos, total_salidas, usuario))

    # Marcar como cerrados esos ingresos
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
        "Total recaudado": f"${total_recaudado}",
        "Total ingresos": total_ingresos,
        "Total salidas": total_salidas,
        "Registrado por": usuario
    }
    generar_pdf_cierre("diario", datos_pdf)

    cursor.close()
    conn.close()
    return True, f"Cierre realizado con éxito. Total recaudado: ${total_recaudado}"

def realizar_cierre_mensual(usuario):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Obtener el mes más antiguo con ingresos que aún no haya sido cerrado
    cursor.execute("""
        SELECT DATE_FORMAT(MIN(fecha_hora_ingreso), '%Y-%m') AS mes
        FROM ingresos
        WHERE fecha_hora_ingreso IS NOT NULL
          AND DATE_FORMAT(fecha_hora_ingreso, '%Y-%m') NOT IN (
              SELECT mes FROM cierres_mensuales
          )
    """)
    resultado = cursor.fetchone()
    if not resultado or not resultado["mes"]:
        cursor.close()
        conn.close()
        return False, "No hay meses pendientes por cerrar."

    mes_a_cerrar = resultado["mes"]

    # 2. Obtener datos del mes a cerrar
    cursor.execute("""
        SELECT COUNT(*) AS ingresos
        FROM ingresos
        WHERE DATE_FORMAT(fecha_hora_ingreso, '%Y-%m') = %s
    """, (mes_a_cerrar,))
    total_ingresos = cursor.fetchone()["ingresos"]

    cursor.execute("""
        SELECT COUNT(*) AS salidas, SUM(tarifa_aplicada) AS total
        FROM ingresos
        WHERE fecha_hora_salida IS NOT NULL
          AND DATE_FORMAT(fecha_hora_salida, '%Y-%m') = %s
    """, (mes_a_cerrar,))
    salida_info = cursor.fetchone()
    total_salidas = salida_info["salidas"]
    total_recaudado = salida_info["total"] or 0

    # 3. Insertar el cierre mensual
    cursor.execute("""
        INSERT INTO cierres_mensuales (mes, fecha_cierre, total_recaudado, total_ingresos, total_salidas, usuario)
        VALUES (%s, NOW(), %s, %s, %s, %s)
    """, (mes_a_cerrar, total_recaudado, total_ingresos, total_salidas, usuario))

    conn.commit()

    datos_pdf = {
        "Mes": mes_a_cerrar,
        "Fecha de cierre": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Total recaudado": f"${total_recaudado}",
        "Total ingresos": total_ingresos,
        "Total salidas": total_salidas,
        "Registrado por": usuario
    }
    generar_pdf_cierre("mensual", datos_pdf)

    cursor.close()
    conn.close()
    return True, f"Cierre del mes {mes_a_cerrar} realizado correctamente."
