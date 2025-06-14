from fpdf import FPDF
from datetime import datetime
import os
import platform
import subprocess

def generar_ticket_ingreso(patente, fecha_hora):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="ESTACIONAMIENTO CENTRAL", ln=True, align='C')
    pdf.cell(200, 10, txt="Ticket de Ingreso", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(100, 10, txt=f"Patente: {patente}", ln=True)
    pdf.cell(100, 10, txt=f"Fecha y hora de ingreso:", ln=True)
    pdf.cell(100, 10, txt=f"{fecha_hora.strftime('%d-%m-%Y %H:%M:%S')}", ln=True)

    nombre_archivo = f"Ticket_ingreso_{patente}_{fecha_hora.strftime('%Y%m%d%H%M%S')}.pdf"
    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)
    ruta =os.path.join(carpeta, nombre_archivo)
    pdf.output(ruta)
    abrir_pdf(ruta)
    return ruta

def generar_ticket_salida(patente, fecha_hora_ingreso, fecha_hora_salida, tarifa):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="ESTACIONAMIENTO CENTRAL", ln=True, align='C')
    pdf.cell(200, 10, txt="Ticket de salida", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(100, 10, txt=f"Patente: {patente}", ln=True)
    pdf.cell(100, 10, txt=f"Ingreso: {fecha_hora_ingreso.strftime('%d-%m-%Y %H:%M:%S')}", ln=True)
    pdf.cell(100, 10, txt=f"Salida: {fecha_hora_salida.strftime('%d-%m-%Y %H:%M:%S')}", ln=True)
    pdf.cell(100, 10, txt=f"Total a pagar: ${tarifa:.0f}", ln=True)

    nombre_archivo = f"ticket_salida_{patente}_{fecha_hora_salida.strftime('%Y%m%d%H%M%S')}.pdf"
    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre_archivo)
    pdf.output(ruta)
    abrir_pdf(ruta)
    return ruta

def abrir_pdf(ruta):
    if platform.system() == "Windows":
        os.startfile(ruta)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", ruta])
    else:  # Linux
        subprocess.run(["xdg-open", ruta])