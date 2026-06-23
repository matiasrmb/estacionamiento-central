"""
Módulo para generación e impresión de tickets de ingreso y salida
en formato PDF optimizado para impresoras térmicas de 58mm.
"""

from fpdf import FPDF
import os
import platform
import subprocess
from pathlib import Path

from utils.printer_manager import resolver_impresora_tickets


def generar_ticket_ingreso(patente, fecha_hora):
    """
    Genera e imprime automáticamente un ticket de ingreso para un vehículo.
    """
    pdf = FPDF(format=(58, 135), unit="mm")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=4)
    pdf.set_font("Courier", size=13)

    pdf.cell(0, 7, "ESTACIONAMIENTO", ln=True, align="C")
    pdf.cell(0, 7, "CENTRAL", ln=True, align="C")
    pdf.cell(0, 7, "Ticket de Ingreso", ln=True, align="C")
    pdf.cell(0, 5, "-" * 24, ln=True, align="C")
    pdf.cell(0, 7, f"Patente: {patente}", ln=True)
    pdf.cell(0, 7, "Ingreso:", ln=True)
    pdf.cell(0, 7, fecha_hora.strftime("%d-%m-%Y"), ln=True)
    pdf.cell(0, 7, fecha_hora.strftime("Hora: %H:%M:%S"), ln=True)
    pdf.cell(0, 5, "-" * 24, ln=True, align="C")
    pdf.cell(0, 7, "Gracias por su visita", ln=True, align="C")

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
    modo_cobro="minuto",
    total_lavados=0,
    tarifa_estacionamiento=None,
    detalle_cobro=None,
):
    """
    Genera e imprime automáticamente un ticket de salida para un vehículo.

    Args:
        patente (str): Patente del vehículo.
        fecha_hora_ingreso (datetime): Fecha y hora de ingreso.
        fecha_hora_salida (datetime): Fecha y hora de salida.
        tarifa (int or float): Monto total a pagar, incluyendo lavados.
        subida_aplicada (bool): Indica si hubo subida temporal aplicada.
        monto_extra (int or float): Monto extra aplicado por subida temporal.
        minutos (int, optional): Minutos totales de permanencia.
        modo_cobro (str): Modo de cobro aplicado ("minuto", "personalizado", "auto").
        total_lavados (int or float): Total por lavados asociados a la estadía.
        tarifa_estacionamiento (int or float, optional): Subtotal por estacionamiento.
        detalle_cobro (str, optional): Detalle legible del tramo/modo cobrado.

    Returns:
        str: Ruta del archivo PDF generado.
    """
    pdf = FPDF(format=(58, 185), unit="mm")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=4)
    pdf.set_font("Courier", size=13)

    pdf.cell(0, 7, "ESTACIONAMIENTO", ln=True, align="C")
    pdf.cell(0, 7, "CENTRAL", ln=True, align="C")
    pdf.cell(0, 7, "Ticket de Salida", ln=True, align="C")
    pdf.cell(0, 5, "-" * 24, ln=True, align="C")

    pdf.cell(0, 7, f"Patente: {patente}", ln=True)
    pdf.cell(0, 7, "Ingreso:", ln=True)
    pdf.cell(0, 7, fecha_hora_ingreso.strftime("%d-%m-%Y %H:%M:%S"), ln=True)
    pdf.cell(0, 7, "Salida:", ln=True)
    pdf.cell(0, 7, fecha_hora_salida.strftime("%d-%m-%Y %H:%M:%S"), ln=True)

    if minutos is not None:
        pdf.cell(0, 7, f"Tiempo: {minutos} min", ln=True)

    pdf.cell(0, 5, "-" * 24, ln=True, align="C")

    # Mostrar modo de cobro
    modo_legible = {
        "minuto": "Por minuto",
        "personalizado": "Tramos",
        "auto": "Automatico"
    }.get(modo_cobro, modo_cobro)

    pdf.cell(0, 7, f"Modo: {modo_legible}", ln=True)

    if detalle_cobro:
        pdf.multi_cell(0, 7, f"Detalle: {detalle_cobro}")

    if subida_aplicada:
        pdf.cell(0, 7, f"Subida: +${monto_extra:.0f}", ln=True)

    if tarifa_estacionamiento is not None:
        pdf.cell(0, 7, f"Estac: ${tarifa_estacionamiento:.0f}", ln=True)

    if total_lavados:
        pdf.cell(0, 7, f"Lavados: ${total_lavados:.0f}", ln=True)

    pdf.cell(0, 5, "-" * 24, ln=True, align="C")
    pdf.set_font("Courier", size=14)
    pdf.cell(0, 8, f"TOTAL: ${tarifa:.0f}", ln=True, align="C")
    pdf.set_font("Courier", size=13)
    pdf.cell(0, 5, "-" * 24, ln=True, align="C")
    pdf.cell(0, 7, "Gracias por su visita", ln=True, align="C")

    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"ticket_salida_{patente}_{fecha_hora_salida.strftime('%Y%m%d%H%M%S')}.pdf"
    ruta = os.path.join(carpeta, nombre)

    pdf.output(ruta)
    imprimir_pdf_directamente(ruta)
    return ruta

def obtener_ruta_sumatra() -> str | None:
    """
    Busca SumatraPDF en rutas comunes de Windows.

    Returns:
        str | None: Ruta del ejecutable si existe, o None.
    """
    rutas_posibles = [
        Path(r"C:\Program Files\SumatraPDF\SumatraPDF.exe"),
        Path(r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe"),
        Path.home() / r"AppData\Local\SumatraPDF\SumatraPDF.exe",
    ]

    for ruta in rutas_posibles:
        if ruta.is_file():
            return str(ruta)

    return None

def imprimir_pdf_directamente(ruta, nombre_impresora=None):
    """
    Envía un archivo PDF a imprimir directamente usando SumatraPDF.

    Si no se especifica impresora, el sistema intenta resolverla
    automáticamente desde config.ini o desde Windows.

    Args:
        ruta (str): Ruta del archivo PDF.
        nombre_impresora (str | None): Nombre opcional de la impresora.

    Returns:
        bool: True si el comando fue lanzado correctamente, False en caso contrario.
    """
    try:
        if not os.path.isfile(ruta):
            raise FileNotFoundError(f"No existe el PDF: {ruta}")

        ruta_sumatra = obtener_ruta_sumatra()
        if not ruta_sumatra:
            raise FileNotFoundError(
                "No se encontró SumatraPDF en rutas conocidas."
            )

        impresora = nombre_impresora or resolver_impresora_tickets()
        if not impresora:
            raise RuntimeError(
                "No hay impresoras disponibles o configuradas en el sistema."
            )

        comando = [
            ruta_sumatra,
            "-print-to", impresora,
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
