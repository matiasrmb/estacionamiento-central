import bcrypt
from utils.db import get_connection

def validar_usuario(usuario, clave_plana):
    conn = get_connection()
    if conn is None:
        return False, None # No hay conexión
    
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM usuarios WHERE usuario = %s"
    cursor.execute(query, (usuario,))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if resultado:
        if not resultado.get("activo", 1):
            return "inactivo", None  # Usuario existe, pero desactivado

        clave_hash = resultado["clave_hash"].encode("utf-8")
        if bcrypt.checkpw(clave_plana.encode("utf-8"), clave_hash):
            registrar_asistencia_inicio(usuario)  # 👈 se registra aquí
            return True, resultado["rol"]

    return False, None  # Usuario no existe o clave incorrecta

def registrar_asistencia_inicio(usuario):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO asistencias (usuario, hora_inicio)
        VALUES (%s, NOW())
    """, (usuario,))
    conn.commit()
    cursor.close()
    conn.close()

def registrar_asistencia_salida(usuario):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE asistencias
        SET hora_salida = NOW()
        WHERE usuario = %s AND hora_salida IS NULL
        ORDER BY hora_inicio DESC
        LIMIT 1
    """, (usuario,))
    conn.commit()
    cursor.close()
    conn.close()
