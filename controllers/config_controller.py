from utils.db import get_connection

def obtener_configuracion():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT clave, valor FROM configuracion")
    datos = cursor.fetchall()
    cursor.close()
    conn.close()

    return {item["clave"]: item["valor"] for item in datos}

def actualizar_configuracion(clave, valor):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE configuracion SET valor = %s WHERE clave = %s",
        (str(valor), clave)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True

def guardar_configuracion_masiva(diccionario_config):
    conn = get_connection()
    cursor = conn.cursor()
    for clave, valor in diccionario_config.items():
        cursor.execute(
            "UPDATE configuracion SET valor = %s WHERE clave = %s",
            (str(valor), clave)
        )
    conn.commit()
    cursor.close()
    conn.close()
