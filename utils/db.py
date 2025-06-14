import mysql.connector
from configparser import ConfigParser

def get_connection():
    config = ConfigParser
    config.read("config.ini")

    db_config = {
        'host': config.get("mysql", "host"),
        'port': config.getint("mysql", "port"),
        'user': config.get("mysql", "user"),
        'password': config.get("mysql", "password"),
        'database': config.get("mysql", "database")
    }

    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None