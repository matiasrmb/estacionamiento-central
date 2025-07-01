import bcrypt
from utils.db import get_connection
from datetime import datetime, timedelta

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
    cursor = conn.cursor(dictionary=True)

    # 1. Obtener la última asistencia activa
    cursor.execute("""
        SELECT id_asistencia, hora_inicio
        FROM asistencias
        WHERE usuario = %s AND hora_salida IS NULL
        ORDER BY hora_inicio DESC
        LIMIT 1
    """, (usuario,))
    asistencia = cursor.fetchone()

    resumen = {"cantidad": 0, "total": 0, "hora_inicio": None}

    if asistencia:
        id_asistencia = asistencia["id_asistencia"]
        hora_inicio = asistencia["hora_inicio"]

        # 2. Calcular totales
        cursor.execute("""
            SELECT COUNT(*) AS cantidad, SUM(tarifa_aplicada) AS total
            FROM ingresos
            WHERE usuario = %s AND fecha_hora_salida BETWEEN %s AND NOW()
        """, (usuario, hora_inicio))
        resultado = cursor.fetchone()
        cantidad = resultado["cantidad"] or 0
        total = resultado["total"] or 0

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

    conn.commit()
    cursor.close()
    conn.close()

    return resumen
