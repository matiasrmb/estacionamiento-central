"""
Controlador para la gestión de reportes de ingresos y salidas de vehículos.

Este módulo permite:
- Consultar los registros de ingresos y salidas dentro de un rango de fechas.
- Filtrar por patente si se requiere.
- Exportar los resultados a un archivo PDF con resumen del total recaudado.
"""

from utils.db import get_connection
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
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

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
          AND DATE(i.fecha_hora_salida) BETWEEN %s AND %s
    """
    params = [fecha_inicio, fecha_fin]

    if patente:
        query += " AND v.patente = %s"
        params.append(patente)

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

    cursor.close()
    conn.close()
    return resultados

def exportar_pdf(datos, fecha_inicio=None, fecha_fin=None, incluir_banos=False):
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

    if incluir_banos and fecha_inicio and fecha_fin:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) AS cantidad, SUM(monto) AS total
            FROM usos_bano
            WHERE DATE(fecha_hora) BETWEEN %s AND %s
        """, (fecha_inicio, fecha_fin))
        resultado = cursor.fetchone()
        total_banos = resultado["cantidad"] or 0
        monto_banos = resultado["total"] or 0
        cursor.close()
        conn.close()

    for row in datos:
        ingreso = row["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M")
        salida = row["fecha_hora_salida"].strftime("%d-%m-%Y %H:%M")
        tarifa = row["tarifa_aplicada"]
        total += tarifa

        pdf.cell(0, 8, f"{row['patente']} | {ingreso} -> {salida} | ${tarifa:.0f}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Total recaudado: ${total:.0f}", ln=True)

    if incluir_banos:
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, f"Baños registrados: {total_banos}", ln=True)
        pdf.cell(0, 8, f"Total recaudado por baños: ${monto_banos:.0f}", ln=True)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Total general (vehículos + baños): ${total + monto_banos:.0f}", ln=True)

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