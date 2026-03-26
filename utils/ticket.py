"""
Módulo para generación e impresión de tickets de ingreso y salida
en formato PDF optimizado para impresoras térmicas de 58mm.
"""

from fpdf import FPDF
from datetime import datetime
import os
import platform
import subprocess


def generar_ticket_ingreso(patente, fecha_hora):
    """
    Genera e imprime automáticamente un ticket de ingreso para un vehículo.
    """
    pdf = FPDF(format=(58, 90), unit="mm")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=4)
    pdf.set_font("Courier", size=9)

    pdf.cell(0, 5, "ESTACIONAMIENTO CENTRAL", ln=True, align="C")
    pdf.cell(0, 5, "Ticket de Ingreso", ln=True, align="C")
    pdf.cell(0, 4, "-" * 28, ln=True, align="C")
    pdf.cell(0, 5, f"Patente: {patente}", ln=True)
    pdf.cell(0, 5, "Ingreso:", ln=True)
    pdf.cell(0, 5, fecha_hora.strftime("%d-%m-%Y %H:%M:%S"), ln=True)
    pdf.cell(0, 4, "-" * 28, ln=True, align="C")
    pdf.cell(0, 5, "Gracias por su visita", ln=True, align="C")

    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"ticket_ingreso_{patente}_{fecha_hora.strftime('%Y%m%d%H%M%S')}.pdf"
    ruta = os.path.join(carpeta, nombre)

    pdf.output(ruta)
    imprimir_pdf_directamente(ruta)
    return ruta

def generar_ticket_salida(
    patente,
    fecha_hora_ingreso,
    fecha_hora_salida,
    tarifa,
    subida_aplicada=False,
    monto_extra=0,
    minutos=None,
    modo_cobro="minuto"
):
    """
    Genera e imprime automáticamente un ticket de salida para un vehículo.

    Args:
        patente (str): Patente del vehículo.
        fecha_hora_ingreso (datetime): Fecha y hora de ingreso.
        fecha_hora_salida (datetime): Fecha y hora de salida.
        tarifa (int or float): Monto total a pagar.
        subida_aplicada (bool): Indica si hubo subida temporal aplicada.
        monto_extra (int or float): Monto extra aplicado por subida temporal.
        minutos (int, optional): Minutos totales de permanencia.
        modo_cobro (str): Modo de cobro aplicado ("minuto", "personalizado", "auto").

    Returns:
        str: Ruta del archivo PDF generado.
    """
    pdf = FPDF(format=(58, 130), unit="mm")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=4)
    pdf.set_font("Courier", size=9)

    pdf.cell(0, 5, "ESTACIONAMIENTO CENTRAL", ln=True, align="C")
    pdf.cell(0, 5, "Ticket de Salida", ln=True, align="C")
    pdf.cell(0, 4, "-" * 28, ln=True, align="C")

    pdf.cell(0, 5, f"Patente: {patente}", ln=True)
    pdf.cell(0, 5, "Ingreso:", ln=True)
    pdf.cell(0, 5, fecha_hora_ingreso.strftime("%d-%m-%Y %H:%M"), ln=True)
    pdf.cell(0, 5, "Salida:", ln=True)
    pdf.cell(0, 5, fecha_hora_salida.strftime("%d-%m-%Y %H:%M"), ln=True)

    if minutos is not None:
        pdf.cell(0, 5, f"Tiempo: {minutos} min", ln=True)

    pdf.cell(0, 4, "-" * 28, ln=True, align="C")

    # Mostrar modo de cobro
    modo_legible = {
        "minuto": "Por minuto",
        "personalizado": "Tramos",
        "auto": "Automatico"
    }.get(modo_cobro, modo_cobro)

    pdf.cell(0, 5, f"Modo cobro: {modo_legible}", ln=True)

    if subida_aplicada:
        pdf.cell(0, 5, f"Subida aplicada: +${monto_extra:.0f}", ln=True)

    pdf.cell(0, 4, "-" * 28, ln=True, align="C")
    pdf.set_font("Courier", size=10)
    pdf.cell(0, 6, f"TOTAL A PAGAR: ${tarifa:.0f}", ln=True, align="C")
    pdf.set_font("Courier", size=9)
    pdf.cell(0, 4, "-" * 28, ln=True, align="C")
    pdf.cell(0, 5, "Gracias por su visita", ln=True, align="C")

    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"ticket_salida_{patente}_{fecha_hora_salida.strftime('%Y%m%d%H%M%S')}.pdf"
    ruta = os.path.join(carpeta, nombre)

    pdf.output(ruta)
    imprimir_pdf_directamente(ruta)
    return ruta


def imprimir_pdf_directamente(ruta, nombre_impresora="POS58 Printer"):
    """
    Envía un archivo PDF a imprimir directamente usando SumatraPDF.

    Args:
        ruta (str): Ruta del archivo PDF.
        nombre_impresora (str): Nombre de la impresora de destino.

    Returns:
        bool: True si el comando fue lanzado correctamente, False en caso contrario.
    """
    ruta_sumatra = r"C:\Users\matia\AppData\Local\SumatraPDF\SumatraPDF.exe"

    try:
        if not os.path.isfile(ruta):
            raise FileNotFoundError(f"No existe el PDF: {ruta}")

        if not os.path.isfile(ruta_sumatra):
            raise FileNotFoundError(f"No existe SumatraPDF: {ruta_sumatra}")

        comando = [
            ruta_sumatra,
            "-print-to", nombre_impresora,
            "-silent",
            "-exit-on-print",
            ruta
        ]

        subprocess.Popen(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True

    except Exception as e:
        print(f"Error al imprimir el ticket con SumatraPDF: {e}")
        return False

def abrir_pdf(ruta):
    """
    Abre un archivo PDF con el visor predeterminado del sistema.

    Args:
        ruta (str): Ruta absoluta del archivo PDF.
    """
    if platform.system() == "Windows":
        os.startfile(ruta)
    elif platform.system() == "Darwin":
        subprocess.run(["open", ruta])
    else:
        subprocess.run(["xdg-open", ruta])