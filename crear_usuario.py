import bcrypt
from utils.db import get_connection

def crear_usuario(usuario, clave_plana, rol):
    conn = get_connection()
    cursor = conn.cursor()

    clave_hash = bcrypt.hashpw(clave_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor.execute("""
        INSERT INTO usuarios (usuario, clave_hash, rol)
        VALUES (%s, %s, %s)
    """, (usuario, clave_hash, rol))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Usuario {usuario} creado exitosamente con rol '{rol}'.")