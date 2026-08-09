"""
Controlador para la gestión de reportes de ingresos y salidas de vehículos.

Este módulo permite:
- Consultar los registros de ingresos y salidas dentro de un rango de fechas.
- Filtrar por patente si se requiere.
- Exportar los resultados a un archivo PDF con resumen del total recaudado.
"""

from utils.db import db_cursor
from utils.pdf_utils import ReportePDF, abrir_pdf
from datetime import datetime, time
from fpdf import FPDF
import os

def obtener_reportes(fecha_inicio, fecha_fin, patente=""):
    """
    Obtiene los registros de ingresos y salidas de vehículos dentro de un rango de fechas.

    Args:
        fecha_inicio (date): Fecha inicial del rango a consultar.
        fecha_fin (date): Fecha final del rango a consultar.
        patente (str, opcional): Patente del vehículo para filtrar resultados. Por defecto, devuelve todos.

    Returns:
        list[dict]: Lista de movimientos con campos: patente, ingreso, salida, minutos y tarifa_aplicada.
    """
    query = """
        SELECT 
            v.patente,
            i.fecha_hora_ingreso,
            i.fecha_hora_salida,
            TIMESTAMPDIFF(MINUTE, i.fecha_hora_ingreso, i.fecha_hora_salida) AS minutos,
            i.tarifa_aplicada
        FROM ingresos i
        JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
        WHERE i.fecha_hora_salida IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM ingresos_eliminados ie
              WHERE ie.id_ingreso_original = i.id_ingreso
          )
          AND DATE(i.fecha_hora_salida) BETWEEN %s AND %s
    """
    params = [fecha_inicio, fecha_fin]

    if patente:
        query += " AND v.patente = %s"
        params.append(patente)

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, tuple(params))
        resultados = cursor.fetchall()

        # Usos de baños (solo si no se filtró patente)
        if not patente:
            cursor.execute("""
                SELECT fecha_hora, monto, usuario
                FROM usos_bano
                WHERE DATE(fecha_hora) BETWEEN %s AND %s
            """, (fecha_inicio, fecha_fin))
            banos = cursor.fetchall()
            for b in banos:
                resultados.append({
                    "patente": "[BAÑO]",
                    "fecha_hora_ingreso": b["fecha_hora"],
                    "fecha_hora_salida": b["fecha_hora"],
                    "minutos": 0,
                    "tarifa_aplicada": b["monto"]
                })

            cursor.execute("""
                SELECT patente, fecha_hora_inicio, fecha_hora_fin,
                       TIMESTAMPDIFF(MINUTE, fecha_hora_inicio, fecha_hora_fin) AS minutos,
                       valor_lavado_snapshot
                FROM operaciones_servicio
                WHERE estado = 'FINALIZADO_COBRADO'
                  AND id_ingreso_generado IS NULL
                  AND fecha_hora_fin IS NOT NULL
                  AND DATE(fecha_hora_fin) BETWEEN %s AND %s
                ORDER BY fecha_hora_fin
            """, (fecha_inicio, fecha_fin))
            for lavado in cursor.fetchall():
                resultados.append({
                    "tipo": "lavado_solo",
                    "patente": lavado["patente"],
                    "fecha_hora_ingreso": lavado["fecha_hora_inicio"],
                    "fecha_hora_salida": lavado["fecha_hora_fin"],
                    "minutos": lavado["minutos"] or 0,
                    "tarifa_aplicada": lavado["valor_lavado_snapshot"] or 0,
                })

            cursor.execute("""
                SELECT fecha_hora, monto, descripcion
                FROM gastos_operacion
                WHERE DATE(fecha_hora) BETWEEN %s AND %s
                ORDER BY fecha_hora
            """, (fecha_inicio, fecha_fin))
            for gasto in cursor.fetchall():
                resultados.append({
                    "tipo": "gasto",
                    "patente": "[GASTO]",
                    "fecha_hora_ingreso": gasto["fecha_hora"],
                    "fecha_hora_salida": gasto["fecha_hora"],
                    "minutos": 0,
                    "tarifa_aplicada": -(gasto["monto"] or 0),
                })
        else:
            cursor.execute("""
                SELECT patente, fecha_hora_inicio, fecha_hora_fin,
                       TIMESTAMPDIFF(MINUTE, fecha_hora_inicio, fecha_hora_fin) AS minutos,
                       valor_lavado_snapshot
                FROM operaciones_servicio
                WHERE patente = %s
                  AND estado = 'FINALIZADO_COBRADO'
                  AND id_ingreso_generado IS NULL
                  AND fecha_hora_fin IS NOT NULL
                  AND DATE(fecha_hora_fin) BETWEEN %s AND %s
                ORDER BY fecha_hora_fin
            """, (patente, fecha_inicio, fecha_fin))
            for lavado in cursor.fetchall():
                resultados.append({
                    "tipo": "lavado_solo",
                    "patente": lavado["patente"],
                    "fecha_hora_ingreso": lavado["fecha_hora_inicio"],
                    "fecha_hora_salida": lavado["fecha_hora_fin"],
                    "minutos": lavado["minutos"] or 0,
                    "tarifa_aplicada": lavado["valor_lavado_snapshot"] or 0,
                })

        pagos_query = """
            SELECT v.patente, p.periodo, p.fecha_pago, p.monto_snapshot
            FROM pagos_mensuales p
            JOIN vehiculos v ON p.id_vehiculo = v.id_vehiculo
            WHERE DATE(p.fecha_pago) BETWEEN %s AND %s
        """
        pagos_params = [fecha_inicio, fecha_fin]
        if patente:
            pagos_query += " AND v.patente = %s"
            pagos_params.append(patente)
        pagos_query += " ORDER BY p.fecha_pago"
        cursor.execute(pagos_query, tuple(pagos_params))
        for pago in cursor.fetchall():
            resultados.append({
                "tipo": "mensualidad",
                "patente": f"[MENSUAL] {pago['patente']}",
                "fecha_hora_ingreso": pago["fecha_pago"],
                "fecha_hora_salida": pago["fecha_pago"],
                "minutos": 0,
                "tarifa_aplicada": pago["monto_snapshot"],
            })

        noches_query = """
            SELECT v.patente, c.fecha_hora_pago, c.monto_snapshot
            FROM cobros_noches c
            JOIN ingresos i ON i.id_ingreso = c.id_ingreso
            JOIN vehiculos v ON v.id_vehiculo = i.id_vehiculo
            WHERE c.estado = 'PAGADO'
              AND NOT EXISTS (
                  SELECT 1 FROM ingresos_eliminados ie
                  WHERE ie.id_ingreso_original = i.id_ingreso
              )
              AND DATE(c.fecha_hora_pago) BETWEEN %s AND %s
        """
        noches_params = [fecha_inicio, fecha_fin]
        if patente:
            noches_query += " AND v.patente = %s"
            noches_params.append(patente)
        noches_query += " ORDER BY c.fecha_hora_pago, c.id_cobro_noche"
        cursor.execute(noches_query, tuple(noches_params))
        for cobro in cursor.fetchall():
            resultados.append({
                "tipo": "noche",
                "patente": f"[NOCHES] {cobro['patente']}",
                "fecha_hora_ingreso": cobro["fecha_hora_pago"],
                "fecha_hora_salida": cobro["fecha_hora_pago"],
                "minutos": 0,
                "tarifa_aplicada": cobro["monto_snapshot"],
            })

    resultados.sort(key=lambda item: item["fecha_hora_salida"])
    return resultados

def exportar_pdf(datos, fecha_inicio=None, fecha_fin=None, incluir_banos=False, patente=""):
    """
    Exporta los resultados de los reportes a un archivo PDF con formato estandarizado.

    El archivo se guarda en la carpeta `reportes` con un nombre que incluye el rango de fechas o timestamp.

    Args:
        datos (list[dict]): Lista de movimientos obtenidos con `obtener_reportes`.
        fecha_inicio (date, opcional): Fecha inicial del filtro (para el nombre del archivo).
        fecha_fin (date, opcional): Fecha final del filtro (para el nombre del archivo).
    """
    pdf = ReportePDF("Reporte de Ingresos y Salidas")
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    total = 0
    total_banos = 0
    monto_banos = 0
    lavados_solos = [row for row in datos if row.get("tipo") == "lavado_solo"]
    total_lavados = len(lavados_solos)
    monto_lavados = sum(row.get("tarifa_aplicada") or 0 for row in lavados_solos)
    total_mensualidades = 0
    monto_mensualidades = 0
    total_noches = 0
    monto_noches = 0

    if fecha_inicio and fecha_fin:
        with db_cursor(dictionary=True) as cursor:
            if incluir_banos:
                cursor.execute("""
                    SELECT COUNT(*) AS cantidad, SUM(monto) AS total
                    FROM usos_bano
                    WHERE DATE(fecha_hora) BETWEEN %s AND %s
                """, (fecha_inicio, fecha_fin))
                resultado = cursor.fetchone()
                total_banos = resultado["cantidad"] or 0
                monto_banos = resultado["total"] or 0

            pagos_query = """
                SELECT COUNT(*) AS cantidad, SUM(p.monto_snapshot) AS total
                FROM pagos_mensuales p
                JOIN vehiculos v ON p.id_vehiculo = v.id_vehiculo
                WHERE DATE(p.fecha_pago) BETWEEN %s AND %s
            """
            pagos_params = [fecha_inicio, fecha_fin]
            if patente:
                pagos_query += " AND v.patente = %s"
                pagos_params.append(patente)
            cursor.execute(pagos_query, tuple(pagos_params))
            resultado_mensualidades = cursor.fetchone()
            total_mensualidades = resultado_mensualidades["cantidad"] or 0
            monto_mensualidades = resultado_mensualidades["total"] or 0

            noches_query = """
                SELECT COUNT(*) AS cantidad, SUM(c.monto_snapshot) AS total
                FROM cobros_noches c
                JOIN ingresos i ON i.id_ingreso = c.id_ingreso
                JOIN vehiculos v ON v.id_vehiculo = i.id_vehiculo
                WHERE c.estado = 'PAGADO'
                  AND NOT EXISTS (
                      SELECT 1 FROM ingresos_eliminados ie
                      WHERE ie.id_ingreso_original = i.id_ingreso
                  )
                  AND DATE(c.fecha_hora_pago) BETWEEN %s AND %s
            """
            noches_params = [fecha_inicio, fecha_fin]
            if patente:
                noches_query += " AND v.patente = %s"
                noches_params.append(patente)
            cursor.execute(noches_query, tuple(noches_params))
            resultado_noches = cursor.fetchone()
            total_noches = resultado_noches["cantidad"] or 0
            monto_noches = resultado_noches["total"] or 0

    for row in datos:
        ingreso = row["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M")
        salida = row["fecha_hora_salida"].strftime("%d-%m-%Y %H:%M")
        tarifa = row["tarifa_aplicada"]
        total += tarifa

        pdf.cell(0, 8, f"{row['patente']} | {ingreso} -> {salida} | ${tarifa:.0f}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Total neto: ${total:.0f}", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Mensualidades cobradas: {total_mensualidades}", ln=True)
    pdf.cell(0, 8, f"Total recaudado por mensualidades: ${monto_mensualidades:.0f}", ln=True)
    pdf.cell(0, 8, f"Noches prepagadas cobradas: {total_noches}", ln=True)
    pdf.cell(0, 8, f"Total recaudado por Noches prepagadas: ${monto_noches:.0f}", ln=True)

    if incluir_banos:
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, f"Baños registrados: {total_banos}", ln=True)
        pdf.cell(0, 8, f"Total recaudado por baños: ${monto_banos:.0f}", ln=True)
        pdf.cell(0, 8, f"Lavados independientes registrados: {total_lavados}", ln=True)
        pdf.cell(0, 8, f"Total por lavados independientes: ${monto_lavados:.0f}", ln=True)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Total neto (vehículos, baños, lavados, mensualidades y noches): ${total:.0f}", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 6, "Nota: los lavados vinculados a una estadía se incluyen en el importe del vehículo.", ln=True)

    carpeta = "reportes"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = "reporte_ingresos"
    if fecha_inicio and fecha_fin:
        nombre_archivo += f"_{fecha_inicio.strftime('%Y%m%d')}_a_{fecha_fin.strftime('%Y%m%d')}"
    else:
        nombre_archivo += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ruta = os.path.join(carpeta, nombre_archivo + ".pdf")

    pdf.output(ruta)
    abrir_pdf(ruta)
