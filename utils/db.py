"""
Módulo de conexión a la base de datos MySQL utilizando configuración desde config.ini.
"""

import os
import sys
import mysql.connector
from configparser import ConfigParser


def get_base_path():
    """
    Retorna la ruta base correcta tanto en desarrollo como en ejecutable PyInstaller.
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_connection():
    """
    Establece y retorna una conexión a la base de datos MySQL utilizando
    los datos del archivo config.ini.
    """
    base_path = get_base_path()
    config_path = os.path.join(base_path, "config.ini")

    config = ConfigParser()
    archivos = config.read(config_path, encoding="utf-8")

    if not archivos:
        print(f"No se encontró config.ini en: {config_path}")
        return None

    if not config.has_section("mysql"):
        print("El archivo config.ini no contiene la sección [mysql].")
        return None

    db_config = {
        "host": config.get("mysql", "host"),
        "port": config.getint("mysql", "port"),
        "user": config.get("mysql", "user"),
        "password": config.get("mysql", "password"),
        "database": config.get("mysql", "database"),
    }

    try:
        connection = mysql.connector.connect(charset="utf8mb4", **db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None