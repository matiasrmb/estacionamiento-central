"""
Controlador para la gestión de clientes mensuales del sistema de estacionamiento.
"""

from utils.db import db_cursor

def obtener_mensuales():
    """
    Obtiene una lista de vehículos registrados como clientes mensuales activos.

    Returns:
        list: Lista de diccionarios con 'id_vehiculo', 'patente' y 'tarifa_mensual'.
    """
    query = "SELECT id_vehiculo, patente, tarifa_mensual FROM vehiculos WHERE tipo_cliente = 'mensual' AND activo = 1"

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query)
        resultados = cursor.fetchall()

    return resultados

def agregar_mensual(patente):
    """
    Agrega o actualiza una patente como cliente mensual.

    Args:
        patente (str): Patente del vehículo.

    Returns:
        bool: True si la operación fue exitosa.
    """
    with db_cursor(commit=True) as cursor:
        # Verificar si ya existe como mensual
        cursor.execute("SELECT * FROM vehiculos WHERE patente = %s", (patente,))
        existente = cursor.fetchone()

        if existente:
            cursor.execute(
                "UPDATE vehiculos SET tipo_cliente = 'mensual', activo = 1 WHERE patente = %s",
                (patente,)
            )
        else:
            cursor.execute(
                "INSERT INTO vehiculos (patente, tipo_cliente, activo) VALUES (%s, 'mensual', 1)",
                (patente,)
            )

    return True

def eliminar_mensual(id_vehiculo):
    """
    Desactiva a un cliente mensual (no elimina el registro).

    Args:
        id_vehiculo (int): ID del vehículo.

    Returns:
        bool: True si la operación fue exitosa.
    """
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE vehiculos SET activo = 0 WHERE id_vehiculo = %s",
            (id_vehiculo,)
        )

    return True

def actualizar_tarifa(id_vehiculo, nueva_tarifa):
    """
    Modifica la tarifa mensual asociada a un cliente.

    Args:
        id_vehiculo (int): ID del vehículo.
        nueva_tarifa (int): Nuevo valor de la tarifa mensual.

    Returns:
        bool: True si la operación fue exitosa.
    """
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE vehiculos SET tarifa_mensual = %s WHERE id_vehiculo = %s",
            (nueva_tarifa, id_vehiculo)
        )

    return True
