from utils.pdf_utils import ReportePDF, abrir_pdf
from datetime import datetime
import os

def exportar_asistencias_pdf(asistencias, fecha_inicio=None, fecha_fin=None):
    pdf = ReportePDF("Reporte de Asistencias")
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for row in asistencias:
        inicio = row["hora_inicio"].strftime("%d-%m-%Y %H:%M")
        salida = row["hora_salida"].strftime("%d-%m-%Y %H:%M") if row["hora_salida"] else "En curso"
        linea = (
            f"{row['usuario']} | {inicio} -> {salida} | "
            f"{row['cantidad_movimientos']} movs | ${row['total_recaudado']:.0f}"
        )
        pdf.cell(0, 8, linea, ln=True)

    carpeta = "asistencias"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = "reporte_asistencias"
    if fecha_inicio and fecha_fin:
        nombre_archivo += f"_{fecha_inicio.strftime('%Y%m%d')}_a_{fecha_fin.strftime('%Y%m%d')}"
    else:
        nombre_archivo += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    ruta = os.path.join(carpeta, nombre_archivo + ".pdf")
    pdf.output(ruta)
    abrir_pdf(ruta)
