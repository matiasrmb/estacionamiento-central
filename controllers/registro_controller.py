"""
Controlador de operaciones de ingreso, salida y estado de vehículos en el estacionamiento.
"""

from utils.db import get_connection
from datetime import datetime
from utils.ticket import generar_ticket_ingreso, generar_ticket_salida
from controllers.tarifas_controller import calcular_tarifa
from controllers.subida_controller import obtener_subida_activa

def buscar_estado_vehiculo(patente):
    """
    Determina el estado actual del vehículo (dentro, fuera, o no registrado).

    Args:
        patente (str): Patente del vehículo.

    Returns:
        str: "no_registrado", "dentro" o "fuera".
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Ver si existe el vehículo
        cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s", (patente,))
        vehiculo = cursor.fetchone()

        if not vehiculo:
            return "no_registrado"

        id_vehiculo = vehiculo["id_vehiculo"]

        # 👇 Evitar problema: limpiar resultados anteriores
        cursor.fetchall()

        # 2. Verificar si tiene un ingreso activo
        cursor.execute("""
            SELECT id_ingreso FROM ingresos
            WHERE id_vehiculo = %s AND fecha_hora_salida IS NULL
        """, (id_vehiculo,))
        ingreso_abierto = cursor.fetchone()

        if ingreso_abierto:
            return "dentro"
        else:
            return "fuera"

    finally:
        cursor.close()
        conn.close()

def registrar_ingreso(patente):
    """
    Registra la entrada de un vehículo al estacionamiento.

    Args:
        patente (str): Patente del vehículo.

    Returns:
        bool: True si se registró correctamente.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Ver si ya existe
    cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s", (patente,))
    row = cursor.fetchone()

    if row:
        id_vehiculo = row[0]
    else:
        cursor.execute(
            "INSERT INTO vehiculos (patente, tipo_cliente) VALUES (%s, 'ocasional')",
            (patente,)
        )
        id_vehiculo = cursor.lastrowid

    fecha_hora = datetime.now()
    cursor.execute(
        "INSERT INTO ingresos (id_vehiculo, fecha_hora_ingreso) VALUES (%s, %s)",
        (id_vehiculo, fecha_hora)
    )
    conn.commit()
    cursor.close()
    conn.close()

    generar_ticket_ingreso(patente, fecha_hora)
    return True

def registrar_salida(patente, usuario):
    """
    Registra la salida de un vehículo y calcula la tarifa correspondiente.

    Args:
        patente (str): Patente del vehículo.
        usuario (str): Usuario que registra la salida.

    Returns:
        int or None: Tarifa calculada o None si hubo error.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s", (patente,))
    vehiculo = cursor.fetchone()
    if not vehiculo:
        return None

    id_vehiculo = vehiculo["id_vehiculo"]

    cursor.execute("""
        SELECT * FROM ingresos
        WHERE id_vehiculo = %s AND fecha_hora_salida IS NULL
        ORDER BY fecha_hora_ingreso DESC LIMIT 1
    """, (id_vehiculo,))
    ingreso = cursor.fetchone()

    if not ingreso:
        return None

    fecha_ingreso = ingreso["fecha_hora_ingreso"]
    ahora = datetime.now()
    minutos = int((ahora - fecha_ingreso).total_seconds() / 60)
    tarifa, subida_aplicada, monto_extra = calcular_tarifa(minutos, fecha_ingreso, ahora, devolver_flag=True)

    monto_extra = 0
    if subida_aplicada:
        subida = obtener_subida_activa()
        if subida:
            monto_extra = int(subida["monto_adicional"])

    cursor.execute("""
        UPDATE ingresos
        SET fecha_hora_salida = %s, tarifa_aplicada = %s, usuario = %s
        WHERE id_ingreso = %s
    """, (ahora, tarifa, usuario, ingreso["id_ingreso"]))

    conn.commit()
    cursor.close()
    conn.close()

    generar_ticket_salida(patente, fecha_ingreso, ahora, tarifa, subida_aplicada, monto_extra, minutos)
    return tarifa
    
def obtener_vehiculos_activos():
    """
    Obtiene la lista de vehículos actualmente estacionados.

    Returns:
        list: Lista con patente, hora de ingreso y monto acumulado.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT v.patente, i.fecha_hora_ingreso, i.en_espera
        FROM ingresos i
        JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
        WHERE i.fecha_hora_salida IS NULL
        ORDER BY i.fecha_hora_ingreso ASC
    """)

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    ahora = datetime.now()
    lista = []
    for r in resultados:
        fecha_ingreso = r["fecha_hora_ingreso"]
        minutos = int((ahora - fecha_ingreso).total_seconds() / 60)
        if minutos < 0:
            minutos = 0

        tarifa = calcular_tarifa(minutos, fecha_ingreso, ahora) if r["en_espera"] == 0 else 0

        lista.append({
            "patente": r["patente"] + (" [EN ESPERA]" if r["en_espera"] else ""),
            "hora": fecha_ingreso.strftime("%Y-%m-%d %H:%M:%S"),
            "monto": tarifa,
            "en_espera": bool(r["en_espera"]),
            "minutos": minutos,
        })

    return lista

def obtener_ingresos_editables():
    """
    Obtiene ingresos marcados como 'en espera' o 'cerrados', aún visibles para edición manual.

    Returns:
        list[dict]: Lista con id_ingreso, patente, fecha_hora_ingreso y estado.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Ingresos en espera (no cerrados)
    cursor.execute("""
        SELECT i.id_ingreso, v.patente, i.fecha_hora_ingreso, 'EN ESPERA' AS estado
        FROM ingresos i
        JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
        WHERE i.en_espera = 1 AND i.fecha_hora_salida IS NULL
    """)
    en_espera = cursor.fetchall()

    # Últimos ingresos cerrados en las últimas 24 horas
    cursor.execute("""
        SELECT i.id_ingreso, v.patente, i.fecha_hora_ingreso, 'CERRADO' AS estado
        FROM ingresos i
        JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
        WHERE i.fecha_hora_salida IS NOT NULL AND i.reingresado = 0
        AND i.id_ingreso IN (
            SELECT MAX(i2.id_ingreso)
            FROM ingresos i2
            JOIN vehiculos v2 ON i2.id_vehiculo = v2.id_vehiculo
            WHERE i2.fecha_hora_salida IS NOT NULL AND i2.reingresado = 0
            GROUP BY v2.patente
        )
    """)
    cerrados = cursor.fetchall()

    cursor.close()
    conn.close()

    return en_espera + cerrados

def eliminar_ingreso_con_respaldo(id_ingreso, usuario):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener info original
    cursor.execute("""
        SELECT i.id_ingreso, v.patente, i.fecha_hora_ingreso
        FROM ingresos i
        JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
        WHERE i.id_ingreso = %s
    """, (id_ingreso,))
    ingreso = cursor.fetchone()

    if ingreso:
        # Guardar respaldo
        cursor.execute("""
            INSERT INTO ingresos_eliminados (id_ingreso_original, patente, fecha_hora_ingreso, usuario_eliminador)
            VALUES (%s, %s, %s, %s)
        """, (id_ingreso, ingreso["patente"], ingreso["fecha_hora_ingreso"], usuario))

        # Eliminar el ingreso original
        cursor.execute("DELETE FROM ingresos WHERE id_ingreso = %s", (id_ingreso,))
        conn.commit()

    cursor.close()
    conn.close()

def marcar_ingreso_en_espera(patente):
    """
    Marca el ingreso activo de una patente como 'en espera'.
    Retorna True si se marcó correctamente, False en caso contrario.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Solo si está activo y aún no tiene salida
        cursor.execute("""
            UPDATE ingresos
            SET en_espera = TRUE
            WHERE id_vehiculo = (
                SELECT id_vehiculo FROM vehiculos WHERE patente = %s
            ) AND fecha_hora_salida IS NULL
            ORDER BY fecha_hora_ingreso DESC
            LIMIT 1
        """, (patente,))
        conn.commit()
        exito = cursor.rowcount > 0
        return exito
    except Exception as e:
        print(f"Error al marcar en espera: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def registrar_uso_bano(monto, usuario):
    """
    Registra el uso del baño con el monto entregado.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usos_bano (fecha_hora, monto, usuario)
            VALUES (%s, %s, %s)
        """, (datetime.now(), monto, usuario))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al registrar uso de baño: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def revertir_en_espera(id_ingreso):
    """
    Revierte el estado 'en espera' de un ingreso activo para volverlo a estado normal.

    Args:
        id_ingreso (int): ID del ingreso a revertir.

    Returns:
        bool: True si fue exitoso.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE ingresos
            SET en_espera = 0
            WHERE id_ingreso = %s AND fecha_hora_salida IS NULL
        """, (id_ingreso,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al revertir ingreso en espera: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def reingresar_vehiculo_cerrado(id_ingreso_original):
    """
    Reingresa un vehículo que ya fue cerrado, manteniendo la hora original y la tarifa acumulada.
    Marca el ingreso original como 'reingresado'.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id_vehiculo, fecha_hora_ingreso, tarifa_aplicada
            FROM ingresos
            WHERE id_ingreso = %s AND fecha_hora_salida IS NOT NULL AND reingresado = 0
        """, (id_ingreso_original,))
        ingreso = cursor.fetchone()

        if not ingreso:
            return False

        # Crear nuevo ingreso con misma hora
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ingresos (id_vehiculo, fecha_hora_ingreso, tarifa_aplicada, en_espera)
            VALUES (%s, %s, %s, 0)
        """, (ingreso["id_vehiculo"], ingreso["fecha_hora_ingreso"], ingreso["tarifa_aplicada"]))

        # Marcar el original como reingresado
        cursor.execute("""
            UPDATE ingresos
            SET reingresado = 1
            WHERE id_ingreso = %s
        """, (id_ingreso_original,))

        conn.commit()
        return True

    except Exception as e:
        print(f"Error al reingresar vehículo cerrado: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def alternar_estado_espera(patente):
    """
    Cambia el estado de 'en espera' a normal o viceversa para el ingreso activo de una patente.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id_ingreso, en_espera
            FROM ingresos
            JOIN vehiculos ON ingresos.id_vehiculo = vehiculos.id_vehiculo
            WHERE vehiculos.patente = %s AND fecha_hora_salida IS NULL
            ORDER BY fecha_hora_ingreso DESC
            LIMIT 1
        """, (patente,))
        ingreso = cursor.fetchone()

        if not ingreso:
            return False, "No hay ingreso activo para esta patente."

        if ingreso["en_espera"]:
            exito = revertir_en_espera(ingreso["id_ingreso"])
            return exito, "Revertido de estado 'en espera'." if exito else "No se pudo revertir."
        else:
            exito = marcar_ingreso_en_espera(patente)
            return exito, "Marcado como 'en espera'." if exito else "No se pudo marcar como espera."
    except Exception as e:
        print(f"Error en alternar_estado_espera: {e}")
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def obtener_patentes_existentes():
    """
    Obtiene las patentes de vehículos que actualmente tienen un ingreso activo
    (es decir, ingresos sin fecha de salida).

    Returns:
        list[str]: Lista de patentes con ingreso abierto.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT v.patente
        FROM ingresos i
        JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
        WHERE i.fecha_hora_salida IS NULL
        ORDER BY v.patente ASC
    """)
    filas = cursor.fetchall()

    cursor.close()
    conn.close()

    # filas es una lista de tuplas (('ABC123',), ('BCD234',)...)
    return [f[0] for f in filas]

