"""
Controlador de operaciones de ingreso, salida y estado de vehículos en el estacionamiento.
"""

from datetime import datetime

from utils.db import get_connection
from utils.ticket import generar_ticket_ingreso, generar_ticket_salida
from controllers.tarifas_controller import calcular_tarifa
from controllers.config_controller import obtener_configuracion


def obtener_ingresos_activos_por_patente(patente):
    """
    Obtiene todos los ingresos activos de una patente, priorizados de forma útil
    para la lógica del sistema.

    Prioridad:
    1. ingresos no marcados en espera
    2. ingresos más recientes

    Args:
        patente (str): Patente del vehículo.

    Returns:
        list[dict]: Lista de ingresos activos de la patente.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                i.id_ingreso,
                i.id_vehiculo,
                i.fecha_hora_ingreso,
                i.fecha_hora_salida,
                i.en_espera,
                i.tarifa_aplicada,
                i.reingresado,
                v.patente
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE v.patente = %s
              AND i.fecha_hora_salida IS NULL
            ORDER BY i.en_espera ASC, i.fecha_hora_ingreso DESC
        """, (patente,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def buscar_estado_vehiculo(patente):
    """
    Determina el estado actual del vehículo.

    Args:
        patente (str): Patente del vehículo.

    Returns:
        str: "no_registrado", "dentro" o "fuera".
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id_vehiculo FROM vehiculos WHERE patente = %s LIMIT 1",
            (patente,)
        )
        vehiculo = cursor.fetchone()

        if not vehiculo:
            return "no_registrado"

        activos = obtener_ingresos_activos_por_patente(patente)

        if activos:
            if len(activos) > 1:
                print(f"[WARN] La patente {patente} tiene {len(activos)} ingresos activos.")
            return "dentro"

        return "fuera"

    except Exception as e:
        print(f"Error en buscar_estado_vehiculo: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def registrar_ingreso(patente):
    """
    Registra la entrada de un vehículo al estacionamiento.

    No permite crear un nuevo ingreso si la patente ya tiene un ingreso activo.

    Args:
        patente (str): Patente del vehículo.

    Returns:
        bool: True si se registró correctamente, False en caso contrario.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        activos = obtener_ingresos_activos_por_patente(patente)
        if activos:
            print(f"[WARN] No se registró ingreso para {patente}: ya existe un ingreso activo.")
            return False

        cursor.execute(
            "SELECT id_vehiculo FROM vehiculos WHERE patente = %s LIMIT 1",
            (patente,)
        )
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

        cursor.execute("""
            INSERT INTO ingresos (id_vehiculo, fecha_hora_ingreso, en_espera)
            VALUES (%s, %s, 0)
        """, (id_vehiculo, fecha_hora))

        conn.commit()

    except Exception as e:
        print(f"Error al registrar ingreso: {e}")
        return False

    finally:
        cursor.close()
        conn.close()

    generar_ticket_ingreso(patente, fecha_hora)
    return True


def registrar_salida(patente, usuario):
    """
    Registra la salida de un vehículo y calcula la tarifa correspondiente.

    Si existieran múltiples ingresos activos por inconsistencia previa,
    se prioriza el ingreso activo normal (no en espera). Si no existe,
    se usa el ingreso en espera más reciente.

    Args:
        patente (str): Patente del vehículo.
        usuario (str): Usuario que registra la salida.

    Returns:
        int | None: Tarifa calculada o None si hubo error.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        activos = obtener_ingresos_activos_por_patente(patente)

        if not activos:
            return None

        if len(activos) > 1:
            print(
                f"[WARN] La patente {patente} tiene {len(activos)} ingresos activos. "
                "Se usará el primero priorizado."
            )

        ingreso = activos[0]

        fecha_ingreso = ingreso["fecha_hora_ingreso"]
        ahora = datetime.now()
        minutos = int((ahora - fecha_ingreso).total_seconds() / 60)
        if minutos < 0:
            minutos = 0

        tarifa, subida_aplicada, monto_extra = calcular_tarifa(
            minutos,
            fecha_ingreso,
            ahora,
            devolver_flag=True
        )

        cursor.execute("""
            UPDATE ingresos
            SET fecha_hora_salida = %s,
                tarifa_aplicada = %s,
                usuario = %s
            WHERE id_ingreso = %s
        """, (ahora, tarifa, usuario, ingreso["id_ingreso"]))

        config = obtener_configuracion()
        modo_cobro = config.get("modo_cobro", "minuto")

        conn.commit()

    except Exception as e:
        print(f"Error al registrar salida: {e}")
        return None

    finally:
        cursor.close()
        conn.close()

    generar_ticket_salida(
        patente=patente,
        fecha_hora_ingreso=fecha_ingreso,
        fecha_hora_salida=ahora,
        tarifa=tarifa,
        subida_aplicada=subida_aplicada,
        monto_extra=monto_extra,
        minutos=minutos,
        modo_cobro=modo_cobro
    )
    return tarifa


def obtener_vehiculos_activos():
    """
    Obtiene la lista de vehículos actualmente estacionados.

    Returns:
        list[dict]: Lista con patente, hora de ingreso y monto acumulado.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                i.id_ingreso,
                v.patente,
                i.fecha_hora_ingreso,
                i.en_espera
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.fecha_hora_salida IS NULL
            ORDER BY i.fecha_hora_ingreso ASC
        """)
        resultados = cursor.fetchall()

    finally:
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
            "id_ingreso": r["id_ingreso"],
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

    try:
        cursor.execute("""
            SELECT i.id_ingreso, v.patente, i.fecha_hora_ingreso, 'EN ESPERA' AS estado
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.en_espera = 1 AND i.fecha_hora_salida IS NULL
        """)
        en_espera = cursor.fetchall()

        cursor.execute("""
            SELECT i.id_ingreso, v.patente, i.fecha_hora_ingreso, 'CERRADO' AS estado
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.fecha_hora_salida IS NOT NULL
              AND i.reingresado = 0
              AND i.id_ingreso IN (
                  SELECT MAX(i2.id_ingreso)
                  FROM ingresos i2
                  JOIN vehiculos v2 ON i2.id_vehiculo = v2.id_vehiculo
                  WHERE i2.fecha_hora_salida IS NOT NULL
                    AND i2.reingresado = 0
                  GROUP BY v2.patente
              )
        """)
        cerrados = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return en_espera + cerrados


def eliminar_ingreso_con_respaldo(id_ingreso, usuario):
    """
    Elimina un ingreso y lo respalda previamente en la tabla ingresos_eliminados.

    Args:
        id_ingreso (int): ID del ingreso a eliminar.
        usuario (str): Usuario que realiza la eliminación.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT i.id_ingreso, v.patente, i.fecha_hora_ingreso
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.id_ingreso = %s
        """, (id_ingreso,))
        ingreso = cursor.fetchone()

        if ingreso:
            cursor.execute("""
                INSERT INTO ingresos_eliminados (
                    id_ingreso_original,
                    patente,
                    fecha_hora_ingreso,
                    usuario_eliminador
                )
                VALUES (%s, %s, %s, %s)
            """, (
                id_ingreso,
                ingreso["patente"],
                ingreso["fecha_hora_ingreso"],
                usuario
            ))

            cursor.execute("DELETE FROM ingresos WHERE id_ingreso = %s", (id_ingreso,))
            conn.commit()

    finally:
        cursor.close()
        conn.close()


def marcar_ingreso_en_espera(patente):
    """
    Marca como 'en espera' el ingreso activo normal más reciente de una patente.

    Args:
        patente (str): Patente del vehículo.

    Returns:
        bool: True si se marcó correctamente, False en caso contrario.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT i.id_ingreso
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE v.patente = %s
              AND i.fecha_hora_salida IS NULL
              AND i.en_espera = 0
            ORDER BY i.fecha_hora_ingreso DESC
            LIMIT 1
        """, (patente,))
        ingreso = cursor.fetchone()

        if not ingreso:
            return False

        cursor.close()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ingresos
            SET en_espera = 1
            WHERE id_ingreso = %s
        """, (ingreso["id_ingreso"],))

        conn.commit()
        return cursor.rowcount > 0

    except Exception as e:
        print(f"Error al marcar en espera: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def registrar_uso_bano(monto, usuario):
    """
    Registra el uso del baño con el monto entregado.

    Args:
        monto (int | float): Monto del uso de baño.
        usuario (str): Usuario que registra la operación.

    Returns:
        bool: True si el registro fue exitoso, False en caso contrario.
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
        bool: True si fue exitoso, False en caso contrario.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE ingresos
            SET en_espera = 0
            WHERE id_ingreso = %s
              AND fecha_hora_salida IS NULL
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

    Args:
        id_ingreso_original (int): ID del ingreso cerrado original.

    Returns:
        bool: True si fue exitoso, False en caso contrario.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id_vehiculo, fecha_hora_ingreso, tarifa_aplicada
            FROM ingresos
            WHERE id_ingreso = %s
              AND fecha_hora_salida IS NOT NULL
              AND reingresado = 0
        """, (id_ingreso_original,))
        ingreso = cursor.fetchone()

        if not ingreso:
            return False

        # Evitar duplicar un activo si ya existe uno abierto para esa patente
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM ingresos
            WHERE id_vehiculo = %s
              AND fecha_hora_salida IS NULL
        """, (ingreso["id_vehiculo"],))
        activos = cursor.fetchone()

        if activos and activos["total"] > 0:
            print(
                "[WARN] No se pudo reingresar vehículo: ya existe un ingreso activo "
                f"para id_vehiculo={ingreso['id_vehiculo']}."
            )
            return False

        cursor.close()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ingresos (id_vehiculo, fecha_hora_ingreso, tarifa_aplicada, en_espera)
            VALUES (%s, %s, %s, 0)
        """, (
            ingreso["id_vehiculo"],
            ingreso["fecha_hora_ingreso"],
            ingreso["tarifa_aplicada"]
        ))

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
    Alterna el estado de espera del ingreso activo de una patente.

    Prioriza:
    1. revertir un ingreso en espera si existe
    2. en caso contrario, marcar en espera el ingreso activo normal

    Args:
        patente (str): Patente del vehículo.

    Returns:
        tuple[bool, str]: Resultado y mensaje descriptivo.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT i.id_ingreso
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE v.patente = %s
              AND i.fecha_hora_salida IS NULL
              AND i.en_espera = 1
            ORDER BY i.fecha_hora_ingreso DESC
            LIMIT 1
        """, (patente,))
        ingreso_espera = cursor.fetchone()

        if ingreso_espera:
            exito = revertir_en_espera(ingreso_espera["id_ingreso"])
            return exito, "Revertido de estado 'en espera'." if exito else "No se pudo revertir."

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

    try:
        cursor.execute("""
            SELECT DISTINCT v.patente
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.fecha_hora_salida IS NULL
            ORDER BY v.patente ASC
        """)
        filas = cursor.fetchall()
        return [f[0] for f in filas]

    finally:
        cursor.close()
        conn.close()


def eliminar_ingreso_activo_por_patente(patente, usuario):
    """
    Elimina con respaldo el ingreso activo priorizado de una patente.

    Se prioriza:
    1. ingreso activo normal
    2. ingreso activo en espera

    Args:
        patente (str): Patente del vehículo.
        usuario (str): Usuario que realiza la eliminación.

    Returns:
        tuple[bool, str]: Resultado y mensaje.
    """
    try:
        activos = obtener_ingresos_activos_por_patente(patente)

        if not activos:
            return False, "No hay un ingreso activo para esta patente."

        if len(activos) > 1:
            print(
                f"[WARN] La patente {patente} tiene {len(activos)} ingresos activos. "
                "Se eliminará el primero priorizado."
            )

        id_ingreso = activos[0]["id_ingreso"]

        eliminar_ingreso_con_respaldo(id_ingreso, usuario)
        return True, f"Ingreso activo de {patente} eliminado con respaldo."

    except Exception as e:
        print(f"Error al eliminar ingreso activo por patente: {e}")
        return False, "Ocurrió un error al eliminar el ingreso."