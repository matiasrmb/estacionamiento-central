from utils.db import get_connection

def obtener_mensuales():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT id_vehiculo, patente, tarifa_mensual FROM vehiculos WHERE tipo_cliente = 'mensual' AND activo = 1"
    cursor.execute(query)
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()
    return resultados

def agregar_mensual(patente):
    conn = get_connection()
    cursor = conn.cursor()

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

    conn.commit()
    cursor.close()
    conn.close()
    return True

def eliminar_mensual(id_vehiculo):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE vehiculos SET activo = 0 WHERE id_vehiculo = %s",
        (id_vehiculo,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True

def actualizar_tarifa(id_vehiculo, nueva_tarifa):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE vehiculos SET tarifa_mensual = %s WHERE id_vehiculo = %s",
        (nueva_tarifa, id_vehiculo)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True