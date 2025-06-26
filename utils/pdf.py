from fpdf import FPDF
import os
import webbrowser
from datetime import datetime

def generar_pdf_cierre(tipo, datos):
    pdf = FPDF()
    pdf.add_page()

    # Encabezado
    pdf.set_font("Arial", "B", 18)
    titulo = "Cierre Diario" if tipo == "diario" else "Cierre Mensual"
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, "ESTACIONAMIENTO CENTRAL", ln=True, align="C")
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, titulo, ln=True, align="C")
    pdf.ln(10)

    # Datos con estilo tabla
    pdf.set_font("Arial", "", 12)
    pdf.set_fill_color(240, 240, 240)

    for clave, valor in datos.items():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(60, 10, f"{clave}:", border=0, fill=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, str(valor), ln=True, border=0)

    # Pie de página
    pdf.set_y(-25)
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(100)
    pdf.cell(0, 10, f"Generado el {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", align="R")

    # Guardar archivo
    nombre_archivo = f"{tipo}_cierre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    ruta = os.path.join("pdfs", nombre_archivo)
    os.makedirs("pdfs", exist_ok=True)
    pdf.output(ruta)
    webbrowser.open_new(ruta)
