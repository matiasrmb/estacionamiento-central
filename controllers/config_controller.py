"""
Controlador para la gestión de configuración general del sistema.

Incluye funciones para obtener y actualizar parámetros como tarifas, modos de cobro, etc.
"""

from utils.db import db_cursor

def obtener_configuracion():
    """
    Obtiene la configuración general del sistema como un diccionario clave-valor.

    Returns:
        dict: Configuración del sistema.
    """
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("SELECT clave, valor FROM configuracion")
        datos = cursor.fetchall()

    return {item["clave"]: item["valor"] for item in datos}

def actualizar_configuracion(clave, valor):
    """
    Actualiza una clave de configuración específica.

    Args:
        clave (str): Nombre de la clave.
        valor (str/int): Valor a asignar.

    Returns:
        bool: True si se actualizó correctamente.
    """
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE configuracion SET valor = %s WHERE clave = %s",
            (str(valor), clave)
        )
    return True

def guardar_configuracion_masiva(diccionario_config):
    """
    Actualiza múltiples claves de configuración en una sola operación.

    Args:
        diccionario_config (dict): Diccionario clave-valor con los cambios.
    """
    with db_cursor(commit=True) as cursor:
        for clave, valor in diccionario_config.items():
            cursor.execute(
                "UPDATE configuracion SET valor = %s WHERE clave = %s",
                (str(valor), clave)
            )
