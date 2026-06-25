"""
Módulo de gestión de usuarios.

Incluye funciones para listar, crear, actualizar estado y cambiar la contraseña de usuarios.
"""

import bcrypt
from utils.db import db_cursor


def _normalizar_rol(rol):
    normalizado = (rol or "").strip().lower()
    if normalizado in {"administrador", "admin"}:
        return "administrador"
    if normalizado in {"operador", "operator"}:
        return "operador"
    raise ValueError("Rol inválido")

def obtener_usuarios():
    """
    Obtiene todos los usuarios registrados en el sistema.

    Returns:
        list[dict]: Lista de usuarios con sus campos (id_usuario, usuario, rol, activo).
    """
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("SELECT id_usuario, usuario, rol, activo FROM usuarios ORDER BY id_usuario ASC")
        resultados = cursor.fetchall()
    return resultados


def crear_usuario(usuario, clave, rol):
    """
    Crea un nuevo usuario en la base de datos.

    Args:
        usuario (str): Nombre de usuario.
        clave (str): Contraseña en texto plano.
        rol (str): Rol asignado (ej. 'administrador', 'operador').

    Returns:
        bool: True si se creó exitosamente, False si hubo error.
    """
    clave_hash = bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt())
    try:
        rol_db = _normalizar_rol(rol)
        with db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO usuarios (usuario, clave_hash, rol)
                VALUES (%s, %s, %s)
            """, (usuario, clave_hash, rol_db))
        exito = True
    except Exception as e:
        print("Error al crear usuario:", e)
        exito = False

    return exito

def cambiar_contrasena(usuario, nueva_clave):
    """
    Cambia la contraseña de un usuario.

    Args:
        usuario (str): Nombre del usuario.
        nueva_clave (str): Nueva contraseña en texto plano.

    Returns:
        bool: True si el cambio fue exitoso, False si hubo error.
    """
    if not usuario or not nueva_clave:
        return False

    nuevo_hash = bcrypt.hashpw(nueva_clave.encode("utf-8"), bcrypt.gensalt())

    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE usuarios SET clave_hash = %s WHERE usuario = %s",
                (nuevo_hash, usuario)
            )
            exito = cursor.rowcount > 0
    except Exception as e:
        print("Error al cambiar contraseña:", e)
        exito = False

    return exito

def cambiar_estado_usuario(usuario, nuevo_estado):
    """
    Cambia el estado activo/inactivo de un usuario.

    Args:
        usuario (str): Nombre del usuario.
        nuevo_estado (bool): Estado deseado (True = activo, False = inactivo).

    Returns:
        bool: True si el cambio fue exitoso, False si hubo error.
    """
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute("UPDATE usuarios SET activo = %s WHERE usuario = %s", (nuevo_estado, usuario))
        exito = True
    except Exception as e:
        print("Error al cambiar estado del usuario:", e)
        exito = False
        
    return exito
