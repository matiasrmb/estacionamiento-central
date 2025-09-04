from fpdf import FPDF
from datetime import datetime
import os
import platform

def formatear_fecha(dt):
    return dt.strftime("%d-%m-%Y %H:%M")

def abrir_pdf(ruta):
    if platform.system() == "Windows":
        os.startfile(ruta)
    elif platform.system() == "Darwin":
        os.system(f"open {ruta}")
    else:
        os.system(f"xdg-open {ruta}")

class ReportePDF(FPDF):
    def __init__(self, titulo):
        super().__init__()
        self.titulo = titulo
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(15, 15, 15)

    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "ESTACIONAMIENTO CENTRAL", ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, self.titulo, ln=True, align="C")
        self.ln(5)
        self.set_draw_color(100)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 9)
        self.set_text_color(100)
        self.cell(0, 10, f"Generado el {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", align="R")
