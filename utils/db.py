"""
Módulo de conexión a la base de datos MySQL utilizando configuración desde config.ini.
"""

import mysql.connector
from configparser import ConfigParser

def get_connection():
    """
    Establece y retorna una conexión a la base de datos MySQL utilizando los datos del archivo config.ini.

    Returns:
        mysql.connector.connection_cext.CMySQLConnection or None: 
            Objeto de conexión si se conecta exitosamente, o None si ocurre un error.
    """
    config = ConfigParser()
    config.read("config.ini")

    db_config = {
        'host': config.get("mysql", "host"),
        'port': config.getint("mysql", "port"),
        'user': config.get("mysql", "user"),
        'password': config.get("mysql", "password"),
        'database': config.get("mysql", "database")
    }

    try:
        connection = mysql.connector.connect(charset='utf8mb4', **db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None