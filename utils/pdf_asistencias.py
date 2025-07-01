from fpdf import FPDF
from datetime import datetime
import os
import webbrowser

def exportar_asistencias_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Reporte de Asistencias", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 10)

    # Encabezados
    pdf.cell(30, 8, "Usuario", 1)
    pdf.cell(40, 8, "Inicio", 1)
    pdf.cell(40, 8, "Salida", 1)
    pdf.cell(30, 8, "Movimientos", 1)
    pdf.cell(40, 8, "Recaudado", 1)
    pdf.ln()

    for fila in datos:
        pdf.cell(30, 8, fila["usuario"], 1)
        pdf.cell(40, 8, str(fila["hora_inicio"]), 1)
        pdf.cell(40, 8, str(fila["hora_salida"] or "Activo"), 1)
        pdf.cell(30, 8, str(fila["cantidad_movimientos"]), 1)
        pdf.cell(40, 8, f"${fila['total_recaudado']:.0f}", 1)
        pdf.ln()

    nombre = f"asistencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    carpeta = "pdfs"
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    pdf.output(ruta)
    webbrowser.open(ruta)