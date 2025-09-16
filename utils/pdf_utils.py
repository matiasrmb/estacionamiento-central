"""
Utilidades para la generación y apertura de archivos PDF en el sistema Estacionamiento Central.
"""

from fpdf import FPDF
from datetime import datetime
import os
import platform

def formatear_fecha(dt):
    return dt.strftime("%d-%m-%Y %H:%M")

def abrir_pdf(ruta):
    """
    Abre un archivo PDF con el visor predeterminado del sistema operativo.
    """
    sistema = platform.system()
    if sistema == "Windows":
        os.startfile(ruta)
    elif sistema == "Darwin":  # macOS
        os.system(f"open '{ruta}'")
    else:  # Linux y otros
        os.system(f"xdg-open '{ruta}'")


class ReportePDF(FPDF):
    """
    Clase base para la creación de reportes PDF con encabezado y pie de página personalizados.
    """

    def __init__(self, titulo):
        super().__init__()
        self.titulo = titulo
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(15, 15, 15)

    def header(self):
        """Define el encabezado del reporte PDF."""
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "ESTACIONAMIENTO CENTRAL", ln=True, align="C")

        self.set_font("Arial", "B", 12)
        self.cell(0, 10, self.titulo, ln=True, align="C")

        self.ln(5)
        self.set_draw_color(100)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(5)

    def footer(self):
        """Define el pie de página del reporte PDF."""
        self.set_y(-15)
        self.set_font("Arial", "I", 9)
        self.set_text_color(100)
        self.cell(0, 10, f"Generado el {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", align="R")

