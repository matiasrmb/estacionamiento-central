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


def impresora_existe(nombre_impresora: str | None) -> bool:
    """
    Verifica si una impresora existe entre las impresoras instaladas.

    Args:
        nombre_impresora (str | None): Nombre de la impresora.

    Returns:
        bool: True si existe, False en caso contrario.
    """
    if not nombre_impresora:
        return False

    return nombre_impresora in obtener_impresoras_instaladas()


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


def resolver_impresora_tickets() -> str | None:
    """
    Resuelve la impresora a usar para tickets siguiendo esta prioridad:

    1. Impresora guardada en config.ini, si existe.
    2. Impresora predeterminada de Windows, si existe.
    3. Primera impresora instalada disponible.
    4. None si no hay impresoras disponibles.

    Returns:
        str | None: Nombre de la impresora seleccionada o None.
    """
    impresora_guardada = cargar_impresora_guardada()
    if impresora_existe(impresora_guardada):
        return impresora_guardada

    impresora_default = obtener_impresora_predeterminada()
    if impresora_existe(impresora_default):
        return impresora_default

    impresoras = obtener_impresoras_instaladas()
    if impresoras:
        return impresoras[0]

    return None