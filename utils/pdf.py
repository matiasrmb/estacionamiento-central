from fpdf import FPDF
import os
import webbrowser
from datetime import datetime

def generar_pdf_cierre(tipo, datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)

    titulo = "Cierre Diario" if tipo == "diario" else "Cierre Mensual"
    pdf.cell(0, 10, titulo, ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.ln(10)

    for clave, valor in datos.items():
        pdf.cell(0, 10, f"{clave}: {valor}", ln=True)

    nombre_archivo = f"{tipo}_cierre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    ruta = os.path.join("pdfs", nombre_archivo)

    os.makedirs("pdfs", exist_ok=True)
    pdf.output(ruta)
    webbrowser.open_new(ruta)
