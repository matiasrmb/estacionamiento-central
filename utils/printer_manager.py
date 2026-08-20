"""
Utilidades para la detección, validación y persistencia de impresoras
en sistemas Windows para Estacionamiento Central.
"""

from __future__ import annotations

import configparser
from pathlib import Path
import win32print


CONFIG_PATH = Path("config.ini")


def obtener_impresoras_instaladas() -> list[str]:
    """
    Obtiene la lista de impresoras instaladas en Windows.

    Returns:
        list[str]: Lista de nombres de impresoras disponibles.
    """
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    impresoras = win32print.EnumPrinters(flags)

    nombres = []
    for impresora in impresoras:
        nombre = impresora[2]
        if nombre:
            nombres.append(nombre)

    return sorted(set(nombres), key=str.lower)


def obtener_impresora_predeterminada() -> str | None:
    """
    Obtiene la impresora predeterminada de Windows.

    Returns:
        str | None: Nombre de la impresora predeterminada o None.
    """
    try:
        return win32print.GetDefaultPrinter()
    except Exception:
        return None


def cargar_impresora_guardada(config_path: Path = CONFIG_PATH) -> str | None:
    """
    Carga la impresora de tickets guardada en config.ini.

    Args:
        config_path (Path): Ruta al archivo de configuración.

    Returns:
        str | None: Nombre de la impresora guardada o None.
    """
    if not config_path.exists():
        return None

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    return config.get("impresion", "impresora_tickets", fallback=None)


def guardar_impresora_tickets(nombre_impresora: str, config_path: Path = CONFIG_PATH) -> None:
    """
    Guarda en config.ini la impresora de tickets seleccionada.

    Args:
        nombre_impresora (str): Nombre de la impresora.
        config_path (Path): Ruta al archivo de configuración.
    """
    config = configparser.ConfigParser()

    if config_path.exists():
        config.read(config_path, encoding="utf-8")

    if not config.has_section("impresion"):
        config.add_section("impresion")

    config.set("impresion", "impresora_tickets", nombre_impresora)

    with open(config_path, "w", encoding="utf-8") as archivo:
        config.write(archivo)
