"""
Módulo para generar archivos PDF de cierres diarios o mensuales en el sistema Estacionamiento Central.
"""

from utils.pdf_utils import ReportePDF, abrir_pdf
from datetime import datetime
import os

def generar_pdf_cierre(tipo, datos):
    """
    Genera un PDF con la información de un cierre diario o mensual.

    Args:
        tipo (str): Tipo de cierre. Puede ser 'diario' o 'mensual'.
        datos (dict): Diccionario con los datos a mostrar en el reporte. Las claves serán los títulos.
    """
    titulo = "Cierre Diario" if tipo == "diario" else "Cierre Mensual"
    pdf = ReportePDF(titulo)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for clave, valor in datos.items():
        texto = f"{clave}: {valor}"
        pdf.multi_cell(0, 8, texto)

    # Crear carpeta de salida si no existe
    carpeta = "cierres"
    os.makedirs(carpeta, exist_ok=True)

    # Formatear nombre del archivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f"cierre_{tipo}_{timestamp}.pdf"
    ruta = os.path.join(carpeta, nombre_archivo)

    # Exportar y abrir el PDF
    pdf.output(ruta)
    abrir_pdf(ruta)
