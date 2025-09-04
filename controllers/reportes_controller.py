from utils.db import get_connection
from utils.pdf_utils import ReportePDF, abrir_pdf
from fpdf import FPDF
import os
from datetime import datetime

def obtener_reportes(fecha_inicio, fecha_fin, patente=""):
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

    cursor.close()
    conn.close()
    return resultados

def exportar_pdf(datos, fecha_inicio=None, fecha_fin=None):
    pdf = ReportePDF("Reporte de Ingresos y Salidas")
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    total = 0
    for row in datos:
        ingreso = row["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M")
        salida = row["fecha_hora_salida"].strftime("%d-%m-%Y %H:%M")
        tarifa = row["tarifa_aplicada"]
        total += tarifa

        pdf.cell(0, 8, f"{row['patente']} | {ingreso} -> {salida} | ${tarifa:.0f}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Total recaudado: ${total:.0f}", ln=True)

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