"""
Módulo de conexión a la base de datos MySQL utilizando configuración desde config.ini.
"""

import os
import sys
import mysql.connector
from configparser import ConfigParser


def get_base_paths():
    """
    Retorna rutas candidatas donde buscar config.ini, compatibles con
    desarrollo y con ejecutable generado por PyInstaller.
    """
    paths = []

    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            paths.append(sys._MEIPASS)
        paths.append(os.path.dirname(sys.executable))
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths.append(project_root)

    return paths


def get_connection():
    """
    Establece y retorna una conexión a la base de datos MySQL utilizando
    los datos del archivo config.ini.

    Returns:
        mysql.connector.connection_cext.CMySQLConnection | None:
            Objeto de conexión si se conecta exitosamente, o None si ocurre un error.
    """
    config = ConfigParser()
    config_path = None

    for base_path in get_base_paths():
        candidate = os.path.join(base_path, "config.ini")
        if os.path.exists(candidate):
            config_path = candidate
            break

    if not config_path:
        print("No se encontró config.ini en las rutas esperadas.")
        return None

    archivos = config.read(config_path, encoding="utf-8")
    if not archivos:
        print(f"No se pudo leer config.ini desde: {config_path}")
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