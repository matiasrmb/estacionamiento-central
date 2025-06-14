from utils.db import get_connection
from datetime import datetime
from utils.ticket import generar_ticket_ingreso
from utils.ticket import generar_ticket_salida

def buscar_estado_vehiculo(patente):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Ver si existe el vehículo
    cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s", (patente,))
    vehiculo = cursor.fetchone()

    if not vehiculo:
        cursor.close()
        conn.close()
        return "no_registrado"

    id_vehiculo = vehiculo["id_vehiculo"]

    # Buscar si tiene un ingreso sin salida
    cursor.execute("""
        SELECT id_ingreso FROM ingresos
        WHERE id_vehiculo = %s AND fecha_hora_salida IS NULL
    """, (id_vehiculo,))
    ingreso_abierto = cursor.fetchone()

    cursor.close()
    conn.close()

    if ingreso_abierto:
        return "dentro"
    else:
        return "fuera"

def registrar_ingreso(patente):
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


def registrar_salida(patente):
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
    tarifa = minutos * 50  # Tarifa por minuto

    cursor.execute("""
        UPDATE ingresos SET fecha_hora_salida = %s, tarifa_aplicada = %s
        WHERE id_ingreso = %s
    """, (ahora, tarifa, ingreso["id_ingreso"]))

    conn.commit()
    cursor.close()
    conn.close()

    generar_ticket_salida(patente, fecha_ingreso, ahora, tarifa)
    return tarifa
    

