"""
Controlador de operaciones de ingreso, salida y estado de vehículos en el estacionamiento.
"""

from utils.db import get_connection
from datetime import datetime
from utils.ticket import generar_ticket_ingreso, generar_ticket_salida
from controllers.tarifas_controller import calcular_tarifa

def buscar_estado_vehiculo(patente):
    """
    Determina el estado actual del vehículo (dentro, fuera, o no registrado).

    Args:
        patente (str): Patente del vehículo.

    Returns:
        str: "no_registrado", "dentro" o "fuera".
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Ver si existe el vehículo
        cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s", (patente,))
        vehiculo = cursor.fetchone()

        if not vehiculo:
            return "no_registrado"

        id_vehiculo = vehiculo["id_vehiculo"]

        # 👇 Evitar problema: limpiar resultados anteriores
        cursor.fetchall()

        # 2. Verificar si tiene un ingreso activo
        cursor.execute("""
            SELECT id_ingreso FROM ingresos
            WHERE id_vehiculo = %s AND fecha_hora_salida IS NULL
        """, (id_vehiculo,))
        ingreso_abierto = cursor.fetchone()

        if ingreso_abierto:
            return "dentro"
        else:
            return "fuera"

    finally:
        cursor.close()
        conn.close()

def registrar_ingreso(patente):
    """
    Registra la entrada de un vehículo al estacionamiento.

    Args:
        patente (str): Patente del vehículo.

    Returns:
        bool: True si se registró correctamente.
    """
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor()

    # Ver si ya existe
    cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s", (patente,))
    row = cursor.fetchone()

    if row:
        id_vehiculo = row[0]
    else:
        cursor.execute(
            "INSERT INTO vehiculos (patente, tipo_cliente) VALUES (%s, 'ocasional')",
            (patente,)
        )
        id_vehiculo = cursor.lastrowid

    fecha_hora = datetime.now()
    cursor.execute(
        "INSERT INTO ingresos (id_vehiculo, fecha_hora_ingreso) VALUES (%s, %s)",
        (id_vehiculo, fecha_hora)
    )
    conn.commit()
    cursor.close()
    conn.close()

    generar_ticket_ingreso(patente, fecha_hora)
    return True


def registrar_salida(patente, usuario):
    """
    Registra la salida de un vehículo y calcula la tarifa correspondiente.

    Args:
        patente (str): Patente del vehículo.
        usuario (str): Usuario que registra la salida.

    Returns:
        int or None: Tarifa calculada o None si hubo error.
    """
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s", (patente,))
    vehiculo = cursor.fetchone()
    if not vehiculo:
        return None

    id_vehiculo = vehiculo["id_vehiculo"]

    cursor.execute("""
        SELECT * FROM ingresos
        WHERE id_vehiculo = %s AND fecha_hora_salida IS NULL
        ORDER BY fecha_hora_ingreso DESC LIMIT 1
    """, (id_vehiculo,))
    ingreso = cursor.fetchone()

    if not ingreso:
        return None

    fecha_ingreso = ingreso["fecha_hora_ingreso"]
    ahora = datetime.now()
    minutos = int((ahora - fecha_ingreso).total_seconds() / 60)
    tarifa = calcular_tarifa(minutos)

    cursor.execute("""
        UPDATE ingresos
        SET fecha_hora_salida = %s, tarifa_aplicada = %s, usuario = %s
        WHERE id_ingreso = %s
    """, (ahora, tarifa, usuario, ingreso["id_ingreso"]))

    conn.commit()
    cursor.close()
    conn.close()

    generar_ticket_salida(patente, fecha_ingreso, ahora, tarifa)
    return tarifa
    
def obtener_vehiculos_activos():
    """
    Obtiene la lista de vehículos actualmente estacionados.

    Returns:
        list: Lista con patente, hora de ingreso y monto acumulado.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT v.patente, i.fecha_hora_ingreso, i.en_espera
        FROM ingresos i
        JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
        WHERE i.fecha_hora_salida IS NULL
        ORDER BY i.fecha_hora_ingreso ASC
    """)

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    ahora = datetime.now()
    lista = []
    for r in resultados:
        minutos = int((ahora - r["fecha_hora_ingreso"]).total_seconds() / 60)
        tarifa = calcular_tarifa(minutos) if r["en_espera"] == 0 else 0
        lista.append({
            "patente": r["patente"] + (" [EN ESPERA]" if r["en_espera"] else ""),
            "hora": r["fecha_hora_ingreso"].strftime("%H:%M"),
            "monto": tarifa,
            "en_espera": bool(r["en_espera"])
        })

    return lista