"""
Módulo de control para la gestión de tarifas de estacionamiento.

Este archivo contiene funciones para obtener, agregar, actualizar,
eliminar y calcular tarifas según los modos configurados por el administrador
(minuto a minuto, tramos personalizados o automático).
"""

from utils.db import get_connection
from controllers.config_controller import obtener_configuracion

def obtener_tarifas_personalizadas():
    """
    Obtiene todos los intervalos personalizados de tarifas registrados en la base de datos.

    Returns:
        list[dict]: Lista de tramos con minuto_inicio, minuto_fin y valor.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_tarifa, minuto_inicio, minuto_fin, valor
        FROM tarifas_personalizadas
        ORDER BY minuto_inicio ASC
    """)
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado

def agregar_intervalo(min_inicio, min_fin, valor):
    """
    Agrega un nuevo tramo de tarifa personalizada si no se superpone con otros.

    Args:
        min_inicio (int): Minuto inicial del tramo.
        min_fin (int): Minuto final del tramo.
        valor (int): Valor asociado al tramo.

    Raises:
        ValueError: Si el nuevo tramo se superpone con uno existente.
    """
    if not validar_intervalo(min_inicio, min_fin):
        raise ValueError("❌ El intervalo se superpone con uno existente.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tarifas_personalizadas (minuto_inicio, minuto_fin, valor)
        VALUES (%s, %s, %s)
    """, (min_inicio, min_fin, valor))
    conn.commit()
    cursor.close()
    conn.close()

def actualizar_intervalo(id_tarifa, min_inicio, min_fin, valor):
    """
    Actualiza un tramo de tarifa personalizada.

    Args:
        id_tarifa (int): ID del tramo a actualizar.
        min_inicio (int): Nuevo minuto inicial.
        min_fin (int): Nuevo minuto final.
        valor (int): Nuevo valor del tramo.

    Raises:
        ValueError: Si el nuevo tramo se superpone con otros.
    """
    if not validar_intervalo(min_inicio, min_fin, id_excluir=id_tarifa):
        raise ValueError("❌ El intervalo se superpone con uno existente.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tarifas_personalizadas
        SET minuto_inicio = %s, minuto_fin = %s, valor = %s
        WHERE id_tarifa = %s
    """, (min_inicio, min_fin, valor, id_tarifa))
    conn.commit()
    cursor.close()
    conn.close()


def eliminar_intervalo(id_tarifa):
    """
    Elimina un tramo de tarifa personalizada según su ID.

    Args:
        id_tarifa (int): ID del tramo a eliminar.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tarifas_personalizadas WHERE id_tarifa = %s", (id_tarifa,))
    conn.commit()
    cursor.close()
    conn.close()

def actualizar_intervalo(id_tarifa, min_inicio, min_fin, valor):
    """
    Actualiza un tramo de tarifa personalizada.

    Args:
        id_tarifa (int): ID del tramo a actualizar.
        min_inicio (int): Nuevo minuto inicial.
        min_fin (int): Nuevo minuto final.
        valor (int): Nuevo valor del tramo.

    Raises:
        ValueError: Si el nuevo tramo se superpone con otros.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tarifas_personalizadas
        SET minuto_inicio = %s, minuto_fin = %s, valor = %s
        WHERE id_tarifa = %s
    """, (min_inicio, min_fin, valor, id_tarifa))
    conn.commit()
    cursor.close()
    conn.close()

def calcular_tarifa(minutos):
    """
    Calcula la tarifa según el tiempo transcurrido y el modo configurado.

    Args:
        minutos (int): Tiempo total en minutos.

    Returns:
        int: Valor monetario calculado.
    """
    config = obtener_configuracion()
    modo = config.get("modo_cobro", "minuto")

    if modo == "minuto":
        tarifa_por_minuto = int(config.get("tarifa_hora", 1300)) / 60
        return round(minutos * tarifa_por_minuto)

    elif modo == "personalizado":
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT minuto_inicio, minuto_fin, valor
            FROM tarifas_personalizadas
            ORDER BY minuto_inicio ASC
        """)
        intervalos = cursor.fetchall()
        cursor.close()
        conn.close()

        if not intervalos:
            return int(config.get("tarifa_minima", 300))

        minutos_en_hora = minutos % 60
        horas_completas = minutos // 60

        # Calcular cuánto vale una hora completa (suma de intervalos dentro de 0–59)
        total_hora_base = 0
        for tramo in intervalos:
            if tramo["minuto_fin"] <= 59:
                total_hora_base = tramo["valor"]  # Siempre toma el último válido antes de minuto 60

        # Buscar tramo dentro del ciclo de 0–59
        tarifa_tramo = intervalos[-1]["valor"]  # fallback
        for tramo in intervalos:
            if tramo["minuto_inicio"] <= minutos_en_hora <= tramo["minuto_fin"]:
                tarifa_tramo = tramo["valor"]
                break

        return tarifa_tramo + horas_completas * total_hora_base

    else:
        return int(config.get("tarifa_minima", 300))

def generar_tramos_automaticos():
    """
    Genera tramos de cobro automáticos en bloques de 5 minutos, aumentando $100 por tramo.
    Basado en las tarifas mínimas y por hora desde la configuración.
    """
    config = obtener_configuracion()
    tarifa_min = int(config.get("tarifa_minima", 300))
    tarifa_hora = int(config.get("tarifa_hora", 1300))

    if tarifa_min <= 0 or tarifa_hora <= 0:
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Limpiar tramos actuales
    cursor.execute("DELETE FROM tarifas_personalizadas")

    tramos = []
    valor_actual = tarifa_min
    minutos = 0

    while valor_actual <= tarifa_hora:
        tramo = (minutos, minutos + 4, valor_actual)
        tramos.append(tramo)
        minutos += 5
        valor_actual += 100

    for inicio, fin, valor in tramos:
        cursor.execute("""
            INSERT INTO tarifas_personalizadas (minuto_inicio, minuto_fin, valor)
            VALUES (%s, %s, %s)
        """, (inicio, fin, valor))

    conn.commit()
    cursor.close()
    conn.close()

def validar_intervalo(min_inicio, min_fin, id_excluir=None):
    """
    Valida que un nuevo tramo no se superponga con otros existentes.

    Args:
        min_inicio (int): Minuto inicial.
        min_fin (int): Minuto final.
        id_excluir (int, opcional): ID de tramo a excluir en la validación (en caso de edición).

    Returns:
        bool: True si el tramo es válido (sin superposición).
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if id_excluir:
        cursor.execute("""
            SELECT minuto_inicio, minuto_fin FROM tarifas_personalizadas
            WHERE id_tarifa != %s
        """, (id_excluir,))
    else:
        cursor.execute("SELECT minuto_inicio, minuto_fin FROM tarifas_personalizadas")

    tramos = cursor.fetchall()
    cursor.close()
    conn.close()

    for tramo in tramos:
        if not (min_fin < tramo["minuto_inicio"] or min_inicio > tramo["minuto_fin"]):
            return False  # Hay superposición

    return True
