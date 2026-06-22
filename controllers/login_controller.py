"""
Controlador de login y asistencias.

Permite validar credenciales de usuarios, registrar la asistencia de entrada
y salida, y calcular estadísticas del turno.
"""

import bcrypt
from utils.db import db_cursor
from datetime import datetime, timedelta

def validar_usuario(usuario, clave_plana):
    """
    Verifica si las credenciales ingresadas son válidas.

    Args:
        usuario (str): Nombre del usuario.
        clave_plana (str): Contraseña en texto plano.

    Returns:
        tuple: (resultado de validación: bool|str, rol del usuario: str|None)
    """
    try:
        with db_cursor(dictionary=True) as cursor:
            query = "SELECT * FROM usuarios WHERE usuario = %s"
            cursor.execute(query, (usuario,))
            resultado = cursor.fetchone()
    except Exception as e:
        print(f"Error al validar usuario: {e}")
        return False, None
    
    if resultado:
        if not resultado.get("activo", 1):
            return "inactivo", None  # Usuario existe, pero desactivado

        clave_hash = resultado["clave_hash"].encode("utf-8")
        if bcrypt.checkpw(clave_plana.encode("utf-8"), clave_hash):
            cerrar_asistencias_activas(usuario)
            registrar_asistencia_inicio(usuario)  # 👈 se registra aquí
            return True, resultado["rol"]

    return False, None  # Usuario no existe o clave incorrecta

def registrar_asistencia_inicio(usuario):
    """
    Registra el inicio de turno del usuario actual.

    Args:
        usuario (str): Nombre del usuario.
    """
    with db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO asistencias (usuario, hora_inicio)
            VALUES (%s, NOW())
        """, (usuario,))

def registrar_asistencia_salida(usuario):
    """
    Cierra el turno del usuario actual y calcula resumen de ingresos generados.

    Args:
        usuario (str): Nombre del usuario.

    Returns:
        dict: Contiene 'cantidad', 'total' y 'hora_inicio' del turno cerrado.
    """
    resumen = {"cantidad": 0, "total": 0, "hora_inicio": None}

    with db_cursor(dictionary=True, commit=True) as cursor:
        # 1. Obtener la última asistencia activa
        cursor.execute("""
            SELECT id_asistencia, hora_inicio
            FROM asistencias
            WHERE usuario = %s AND hora_salida IS NULL
            ORDER BY hora_inicio DESC
            LIMIT 1
        """, (usuario,))
        asistencia = cursor.fetchone()

        if asistencia:
            id_asistencia = asistencia["id_asistencia"]
            hora_inicio = asistencia["hora_inicio"]

            cantidad, total = calcular_totales_turno(cursor, usuario, hora_inicio, datetime.now())

            resumen["cantidad"] = cantidad
            resumen["total"] = total
            resumen["hora_inicio"] = hora_inicio

            # 3. Cerrar asistencia
            cursor.execute("""
                UPDATE asistencias
                SET hora_salida = NOW(),
                    total_recaudado = %s,
                    cantidad_movimientos = %s
                WHERE id_asistencia = %s
            """, (total, cantidad, id_asistencia))

    return resumen


def cerrar_asistencias_activas(usuario):
    """
    Cierra asistencias activas previas del usuario.

    Esto evita turnos abiertos si la app o PC se cerró abruptamente y el usuario
    vuelve a iniciar sesión más tarde.
    """
    with db_cursor(dictionary=True, commit=True) as cursor:
        cursor.execute("""
            SELECT id_asistencia, hora_inicio
            FROM asistencias
            WHERE usuario = %s AND hora_salida IS NULL
            ORDER BY hora_inicio ASC
        """, (usuario,))
        asistencias = cursor.fetchall()

        ahora = datetime.now()
        for asistencia in asistencias:
            cantidad, total = calcular_totales_turno(cursor, usuario, asistencia["hora_inicio"], ahora)
            cursor.execute("""
                UPDATE asistencias
                SET hora_salida = %s,
                    total_recaudado = %s,
                    cantidad_movimientos = %s
                WHERE id_asistencia = %s
            """, (ahora, total, cantidad, asistencia["id_asistencia"]))


def calcular_totales_turno(cursor, usuario, hora_inicio, hora_fin):
    cursor.execute("""
        SELECT COUNT(*) AS cantidad, COALESCE(SUM(tarifa_aplicada), 0) AS total
        FROM ingresos
        WHERE usuario = %s AND fecha_hora_salida BETWEEN %s AND %s
    """, (usuario, hora_inicio, hora_fin))
    salidas = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) AS cantidad, COALESCE(SUM(monto), 0) AS total
        FROM usos_bano
        WHERE usuario = %s AND fecha_hora BETWEEN %s AND %s
    """, (usuario, hora_inicio, hora_fin))
    banos = cursor.fetchone()

    cantidad = (salidas["cantidad"] or 0) + (banos["cantidad"] or 0)
    total = (salidas["total"] or 0) + (banos["total"] or 0)
    return cantidad, total

def hay_usuarios_registrados():
    try:
        with db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            resultado = cursor.fetchone()
        return resultado[0] > 0
    except Exception as e:
        print(f"Error al verificar usuarios: {e}")
        return False  # Por defecto, si falla, se asume que no hay usuarios
