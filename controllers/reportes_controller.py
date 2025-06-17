from utils.db import get_connection
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

def exportar_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Reporte de Movimientos", ln=True, align='C')
    pdf.ln(10)

    total = 0
    for row in datos:
        ingreso = row["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M")
        salida = row["fecha_hora_salida"].strftime("%d-%m-%Y %H:%M")
        pdf.cell(200, 10,
            txt=f"{row['patente']} | {ingreso} -> {salida} | ${row['tarifa_aplicada']:.0f}",
            ln=True)
        total += row["tarifa_aplicada"]

    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total recaudado: ${total:.0f}", ln=True)

    carpeta = "reportes"
    os.makedirs(carpeta, exist_ok=True)
    filename = f"reporte_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    path = os.path.join(carpeta, filename)
    pdf.output(path)

    # Abrir automáticamente
    import platform
    if platform.system() == "Windows":
        os.startfile(path)