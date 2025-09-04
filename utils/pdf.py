from utils.pdf_utils import ReportePDF, abrir_pdf
from datetime import datetime
import os

def generar_pdf_cierre(tipo, datos):
    titulo = "Cierre Diario" if tipo == "diario" else "Cierre Mensual"
    pdf = ReportePDF(titulo)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for clave, valor in datos.items():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(60, 8, f"{clave}:", border=0)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, str(valor), ln=True)

    carpeta = "cierres"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = f"cierre_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    ruta = os.path.join(carpeta, nombre_archivo)
    pdf.output(ruta)
    abrir_pdf(ruta)
