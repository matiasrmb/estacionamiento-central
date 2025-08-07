import bcrypt
import argparse
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

    if __name__ == "__main__":
        parser = argparse.ArgumentParser(description="Crear un nuevo usuario en la base de datos.")
        parser.add_argument("usuario", help="Nombre del usuario a crear")
        parser.add_argument("clave", help="Contraseña del usuario")
        parser.add_argument("rol", help="Rol del usuario (admin, usuario, etc.)")

        args = parser.parse_args()
        crear_usuario(args.usuario, args.clave, args.rol)