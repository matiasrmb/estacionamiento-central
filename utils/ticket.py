"""
Módulo para generación e impresión de tickets de ingreso y salida
en formato PDF optimizado para impresoras térmicas de 58mm.
"""

from fpdf import FPDF
from datetime import datetime
import time
import os
import platform
import subprocess

def generar_ticket_ingreso(patente, fecha_hora):
    """
    Genera e imprime automáticamente un ticket de ingreso para un vehículo.

    Args:
        patente (str): Patente del vehículo.
        fecha_hora (datetime): Fecha y hora del ingreso.

    Returns:
        str: Ruta del archivo PDF generado.
    """
    pdf = FPDF(format=(58, 100), unit="mm")
    pdf.add_page()
    pdf.set_font("Courier", size=10)

    pdf.cell(0, 5, "ESTACIONAMIENTO CENTRAL", ln=True, align='C')
    pdf.cell(0, 5, "Ticket de Ingreso", ln=True, align='C')
    pdf.cell(0, 5, "-" * 28, ln=True, align='C')
    pdf.cell(0, 5, f"Patente: {patente}", ln=True)
    pdf.cell(0, 5, "Ingreso:", ln=True)
    pdf.cell(0, 5, fecha_hora.strftime('%d-%m-%Y %H:%M'), ln=True)
    pdf.cell(0, 5, "-" * 28, ln=True, align='C')
    pdf.cell(0, 5, "Gracias por su visita", ln=True, align='C')

    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"Ticket_ingreso_{patente}_{fecha_hora.strftime('%Y%m%d%H%M%S')}.pdf"
    ruta = os.path.join(carpeta, nombre)

    pdf.output(ruta)
    imprimir_pdf_directamente(ruta)
    return ruta

def generar_ticket_salida(patente, fecha_hora_ingreso, fecha_hora_salida, tarifa):
    """
    Genera e imprime automáticamente un ticket de salida para un vehículo.

    Args:
        patente (str): Patente del vehículo.
        fecha_hora_ingreso (datetime): Fecha y hora de ingreso.
        fecha_hora_salida (datetime): Fecha y hora de salida.
        tarifa (int or float): Monto total a pagar.

    Returns:
        str: Ruta del archivo PDF generado.
    """
    pdf = FPDF(format=(58, 120), unit="mm")
    pdf.add_page()
    pdf.set_font("Courier", size=10)

    pdf.cell(0, 5, "ESTACIONAMIENTO CENTRAL", ln=True, align='C')
    pdf.cell(0, 5, "Ticket de Salida", ln=True, align='C')
    pdf.cell(0, 5, "-" * 28, ln=True, align='C')
    pdf.cell(0, 5, f"Patente: {patente}", ln=True)
    pdf.cell(0, 5, "Ingreso:", ln=True)
    pdf.cell(0, 5, fecha_hora_ingreso.strftime('%d-%m-%Y %H:%M'), ln=True)
    pdf.cell(0, 5, "Salida:", ln=True)
    pdf.cell(0, 5, fecha_hora_salida.strftime('%d-%m-%Y %H:%M'), ln=True)
    pdf.cell(0, 5, "-" * 28, ln=True, align='C')
    pdf.cell(0, 5, f"Total a pagar: ${tarifa:.0f}", ln=True, align='C')
    pdf.cell(0, 5, "-" * 28, ln=True, align='C')
    pdf.cell(0, 5, "Gracias por su visita", ln=True, align='C')

    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"ticket_salida_{patente}_{fecha_hora_salida.strftime('%Y%m%d%H%M%S')}.pdf"
    ruta = os.path.join(carpeta, nombre)

    pdf.output(ruta)
    imprimir_pdf_directamente(ruta)
    return ruta

def imprimir_pdf_directamente(ruta):
    """
    Envía el archivo PDF a imprimir directamente a la impresora definida,
    usando Adobe Acrobat Reader en modo silencioso.

    Args:
        ruta (str): Ruta absoluta del archivo PDF.

    Notas:
        - Asegúrate de tener instalado Adobe Acrobat Reader DC.
        - Reemplaza 'POS58 Printer' por el nombre real de tu impresora.
    """ 
    ruta_acrobat = r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe"  # Ajustable
    nombre_impresora = "POS58 Printer"  # Cambiar por nombre real de la impresora

    try:
        # Abrir Acrobat e imprimir silenciosamente
        subprocess.Popen([
            ruta_acrobat,
            '/h',  # Minimiza
            '/t',  # Imprimir
            ruta,
            nombre_impresora
        ])
        time.sleep(2)  # Espera a que se complete la impresión

        # Cierra Acrobat para evitar bloqueos
        subprocess.run(["taskkill", "/f", "/im", "Acrobat.exe"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception as e:
        print(f"Error al imprimir el ticket o cerrar Acrobat Reader: {e}")

def abrir_pdf(ruta):
    """
    Abre un archivo PDF con el visor predeterminado del sistema.

    Args:
        ruta (str): Ruta absoluta del archivo PDF.
    """
    if platform.system() == "Windows":
        os.startfile(ruta)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", ruta])
    else:  # Linux
        subprocess.run(["xdg-open", ruta])
