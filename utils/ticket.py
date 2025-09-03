from fpdf import FPDF
from datetime import datetime
import time
import os
import platform
import subprocess
import platform
import subprocess

def generar_ticket_ingreso(patente, fecha_hora):
    pdf = FPDF(format=(58, 100), unit="mm")  # Formato reducido
    pdf.add_page()
    pdf.set_font("Courier", size=8)

    pdf.cell(0, 5, "ESTACIONAMIENTO CENTRAL", ln=True, align='C')
    pdf.cell(0, 5, "Ticket de Ingreso", ln=True, align='C')
    pdf.cell(0, 5, "-"*28, ln=True, align='C')

    pdf.cell(0, 5, f"Patente: {patente}", ln=True)
    pdf.cell(0, 5, f"Ingreso:", ln=True)
    pdf.cell(0, 5, fecha_hora.strftime('%d-%m-%Y %H:%M'), ln=True)

    pdf.cell(0, 5, "-"*28, ln=True, align='C')
    pdf.cell(0, 5, "Gracias por su visita", ln=True, align='C')

    nombre_archivo = f"Ticket_ingreso_{patente}_{fecha_hora.strftime('%Y%m%d%H%M%S')}.pdf"
    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre_archivo)
    pdf.output(ruta)
    imprimir_pdf_directamente(ruta)
    return ruta

def generar_ticket_salida(patente, fecha_hora_ingreso, fecha_hora_salida, tarifa):
    pdf = FPDF(format=(58, 120), unit="mm")  # Más largo por más datos
    pdf.add_page()
    pdf.set_font("Courier", size=8)

    pdf.cell(0, 5, "ESTACIONAMIENTO CENTRAL", ln=True, align='C')
    pdf.cell(0, 5, "Ticket de Salida", ln=True, align='C')
    pdf.cell(0, 5, "-"*28, ln=True, align='C')

    pdf.cell(0, 5, f"Patente: {patente}", ln=True)
    pdf.cell(0, 5, f"Ingreso:", ln=True)
    pdf.cell(0, 5, fecha_hora_ingreso.strftime('%d-%m-%Y %H:%M'), ln=True)
    pdf.cell(0, 5, f"Salida:", ln=True)
    pdf.cell(0, 5, fecha_hora_salida.strftime('%d-%m-%Y %H:%M'), ln=True)

    pdf.cell(0, 5, "-"*28, ln=True, align='C')
    pdf.cell(0, 5, f"Total a pagar: ${tarifa:.0f}", ln=True, align='C')

    pdf.cell(0, 5, "-"*28, ln=True, align='C')
    pdf.cell(0, 5, "Gracias por su visita", ln=True, align='C')

    nombre_archivo = f"ticket_salida_{patente}_{fecha_hora_salida.strftime('%Y%m%d%H%M%S')}.pdf"
    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre_archivo)
    pdf.output(ruta)
    imprimir_pdf_directamente(ruta)
    return ruta

def imprimir_pdf_directamente(ruta):
    ruta_acrobat = r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe"  # AJUSTA SI ES NECESARIO
    nombre_impresora = "POS58 Printer"  # ← CAMBIA esto por el nombre de tu impresora

    try:
        proceso = subprocess.Popen([
            ruta_acrobat,
            '/h',  
            '/t',  
            ruta,
            nombre_impresora
        ])

        time.sleep(5)  # Espera a que el proceso inicie 

        subprocess.run(["taskkill", "/f", "/im", "Acrobat.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception as e:
        print(f"Error al imprimir el ticket o cerrar Acrobat Reader: {e}")


def abrir_pdf(ruta):
    if platform.system() == "Windows":
        os.startfile(ruta)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", ruta])
    else:  # Linux
        subprocess.run(["xdg-open", ruta])