import bcrypt
from utils.db import get_connection

def obtener_usuarios():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_usuario, usuario, rol FROM usuarios ORDER BY id_usuario ASC")
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

def crear_usuario(usuario, clave, rol):
    conn = get_connection()
    cursor = conn.cursor()
    clave_hash = bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute("""
            INSERT INTO usuarios (usuario, clave_hash, rol)
            VALUES (%s, %s, %s)
        """, (usuario, clave_hash, rol))
        conn.commit()
        exito = True
    except Exception as e:
        print("Error al crear usuario:", e)
        exito = False
    cursor.close()
    conn.close()
    return exito
