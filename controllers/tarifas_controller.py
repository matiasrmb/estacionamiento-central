"""
Módulo de control para la gestión de tarifas de estacionamiento.

Este archivo contiene funciones para obtener, agregar, actualizar,
eliminar y calcular tarifas según los modos configurados por el administrador
(minuto a minuto, tramos personalizados o automático).
"""

from utils.db import get_connection
from datetime import datetime
from controllers.config_controller import obtener_configuracion
from controllers.subida_controller import obtener_subida_activa, calcular_minutos_en_subida

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

def timedelta_to_str(tdelta):
    total_seconds = int(tdelta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02}:{minutes:02}"

def calcular_tarifa(minutos, fecha_hora_ingreso=None, fecha_hora_salida=None, devolver_flag=False):
    """
    Calcula la tarifa según el modo configurado.
    Si devolver_flag=True, retorna (total, subida_aplicada).
    """
    config = obtener_configuracion()
    modo = config["modo_cobro"]
    tarifa_minima = int(config["tarifa_minima"])
    tarifa_hora = int(config["tarifa_hora"])
    total = 0
    subida_aplicada = False
    monto_extra_aplicado = 0

    if modo == "minuto":
        total = tarifa_minima + ((tarifa_hora - tarifa_minima) / 60) * max(minutos - 1, 0)

    elif modo == "personalizado":
        tramos = obtener_tarifas_personalizadas()
        subida = obtener_subida_activa()
        if subida:
            hora_actual = fecha_hora_salida or datetime.now()
            h_inicio_time = datetime.strptime(str(subida["hora_inicio"]), "%H:%M:%S").time()
            h_fin_time = datetime.strptime(str(subida["hora_fin"]), "%H:%M:%S").time()
            h_inicio = datetime.combine(hora_actual.date(), h_inicio_time)
            h_fin = datetime.combine(hora_actual.date(), h_fin_time)
            if h_fin <= h_inicio:
                h_fin = h_fin.replace(day=h_fin.day + 1)

            if h_inicio <= hora_actual <= h_fin:
                subida_aplicada = True
                monto_extra = int(subida["monto_adicional"])
                monto_extra_aplicado = monto_extra
                tramos = [{**tramo, "valor": tramo["valor"] + monto_extra} for tramo in tramos]

        for tramo in tramos:
            if tramo["minuto_inicio"] <= minutos <= tramo["minuto_fin"]:
                total = tramo["valor"]
                break
        else:
            total = tramos[-1]["valor"]

    elif modo == "auto":
        bloques = (minutos // 60) + (1 if minutos % 60 > 0 else 0)
        total = tarifa_minima + ((bloques - 1) * tarifa_minima)
        subida = obtener_subida_activa()
        if subida and fecha_hora_ingreso and fecha_hora_salida:
            minutos_extra = calcular_minutos_en_subida(
                fecha_hora_ingreso, fecha_hora_salida,
                timedelta_to_str(subida["hora_inicio"]),
                timedelta_to_str(subida["hora_fin"])
            )
            if minutos_extra > 0:
                subida_aplicada = True
                monto_extra = (minutos_extra // 5) * int(subida["monto_adicional"])
                total += monto_extra

    return (round(total), subida_aplicada, monto_extra_aplicado) if devolver_flag else round(total)

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
