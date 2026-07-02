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
        with db_cursor(dictionary=True, commit=True) as cursor:
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


def eliminar_usuario_seguro(usuario, usuario_actual=None):
    usuario = (usuario or "").strip()
    usuario_actual = (usuario_actual or "").strip()
    if not usuario:
        return {"ok": False, "action": "blocked", "message": "INVALID_USER_DATA"}

    try:
        with db_cursor(dictionary=True, commit=True) as cursor:
            cursor.execute(
                """
                SELECT usuario, rol, activo
                FROM usuarios
                WHERE usuario = %s
                LIMIT 1
                """,
                (usuario,),
            )
            user = cursor.fetchone()
            if not user:
                return {"ok": False, "action": "blocked", "message": "USER_NOT_FOUND"}

            if usuario_actual and usuario.lower() == usuario_actual.lower():
                return {"ok": False, "action": "blocked", "message": "CANNOT_DELETE_CURRENT_USER"}

            if user["rol"] == "administrador" and int(user.get("activo", 0)) == 1:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS active_admins_after_delete
                    FROM usuarios
                    WHERE rol = 'administrador'
                      AND activo = 1
                      AND usuario <> %s
                    """,
                    (usuario,),
                )
                row = cursor.fetchone() or {}
                if int(row.get("active_admins_after_delete", 0) or 0) == 0:
                    return {"ok": False, "action": "blocked", "message": "CANNOT_DELETE_LAST_ADMIN"}

            if _usuario_tiene_actividad(cursor, usuario):
                cursor.execute("UPDATE usuarios SET activo = %s WHERE usuario = %s", (False, usuario))
                return {"ok": True, "action": "deactivated", "message": "USER_DEACTIVATED_HISTORY_PRESERVED"}

            cursor.execute("DELETE FROM usuarios WHERE usuario = %s", (usuario,))
            return {"ok": True, "action": "deleted", "message": "USER_DELETED"}
    except Exception as e:
        print("Error al eliminar usuario:", e)
        return {"ok": False, "action": "error", "message": "USER_DELETE_ERROR"}


def _usuario_tiene_actividad(cursor, usuario):
    consultas_requeridas = [
        "SELECT 1 AS found FROM ingresos WHERE usuario = %s LIMIT 1",
        "SELECT 1 AS found FROM lavados WHERE usuario_inicio = %s OR usuario_fin = %s LIMIT 1",
        "SELECT 1 AS found FROM usos_bano WHERE usuario = %s LIMIT 1",
        "SELECT 1 AS found FROM cierres_diarios WHERE usuario = %s LIMIT 1",
        "SELECT 1 AS found FROM asistencias WHERE usuario = %s LIMIT 1",
    ]
    consultas_opcionales = [
        ("operaciones_servicio", "SELECT 1 AS found FROM operaciones_servicio WHERE usuario_inicio = %s OR usuario_fin = %s LIMIT 1"),
        ("ingresos_eliminados", "SELECT 1 AS found FROM ingresos_eliminados WHERE usuario_eliminador = %s LIMIT 1"),
        ("print_jobs", "SELECT 1 AS found FROM print_jobs WHERE JSON_SEARCH(payload_json, 'one', %s) IS NOT NULL LIMIT 1"),
    ]

    for consulta in consultas_requeridas:
        parametros = (usuario, usuario) if consulta.count("%s") == 2 else (usuario,)
        cursor.execute(consulta, parametros)
        if cursor.fetchone():
            return True

    for tabla, consulta in consultas_opcionales:
        parametros = (usuario, usuario) if consulta.count("%s") == 2 else (usuario,)
        try:
            cursor.execute(consulta, parametros)
        except Exception as e:
            if _es_error_tabla_faltante(e):
                print(f"Tabla opcional '{tabla}' no encontrada al validar actividad de usuario; se omite.")
                continue
            raise
        if cursor.fetchone():
            return True
    return False


def _es_error_tabla_faltante(error):
    texto = str(error).lower()
    return "doesn't exist" in texto or "no existe" in texto or "unknown table" in texto
