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
            return True, resultado["rol"]

    return False, None  # Usuario no existe o clave incorrecta