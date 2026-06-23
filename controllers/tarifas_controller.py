"""
Módulo de control para la gestión de tarifas de estacionamiento.

Este archivo contiene funciones para obtener, agregar, actualizar,
eliminar y calcular tarifas según los modos configurados por el administrador
(minuto a minuto, tramos personalizados o automático).
"""

from utils.db import db_cursor
from datetime import datetime
from controllers.config_controller import obtener_configuracion
from controllers.subida_controller import obtener_subida_activa, calcular_minutos_en_subida

def obtener_tarifas_personalizadas():
    """
    Obtiene todos los intervalos personalizados de tarifas registrados en la base de datos.

    Returns:
        list[dict]: Lista de tramos con minuto_inicio, minuto_fin y valor.
    """
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id_tarifa, minuto_inicio, minuto_fin, valor
            FROM tarifas_personalizadas
            ORDER BY minuto_inicio ASC
        """)
        resultado = cursor.fetchall()
    return resultado

def obtener_contexto_tarifa():
    """
    Obtiene en una sola vez los datos necesarios para calcular tarifas.

    Útil para pantallas que calculan muchas tarifas en el mismo refresh, como
    el listado de vehículos activos. Evita repetir consultas por cada vehículo.
    """
    config = obtener_configuracion()
    modo = config.get("modo_cobro", "minuto")

    return {
        "config": config,
        "subida": obtener_subida_activa(),
        "tramos": obtener_tarifas_personalizadas() if modo == "personalizado" else [],
    }

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

    with db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO tarifas_personalizadas (minuto_inicio, minuto_fin, valor)
            VALUES (%s, %s, %s)
        """, (min_inicio, min_fin, valor))

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

    with db_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE tarifas_personalizadas
            SET minuto_inicio = %s, minuto_fin = %s, valor = %s
            WHERE id_tarifa = %s
        """, (min_inicio, min_fin, valor, id_tarifa))

def eliminar_intervalo(id_tarifa):
    """
    Elimina un tramo de tarifa personalizada según su ID.

    Args:
        id_tarifa (int): ID del tramo a eliminar.
    """
    with db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM tarifas_personalizadas WHERE id_tarifa = %s", (id_tarifa,))

def timedelta_to_str(tdelta):
    total_seconds = int(tdelta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02}:{minutes:02}"

def calcular_tarifa(minutos, fecha_hora_ingreso=None, fecha_hora_salida=None, devolver_flag=False):
    """
    Calcula la tarifa según el modo configurado.

    Modos soportados:
    - minuto: tarifa mínima + valor por minuto adicional
    - personalizado: tramos personalizados
    - auto: bloques automáticos

    Si devolver_flag=True, retorna:
        (total, subida_aplicada, monto_extra_aplicado)
    """
    return calcular_tarifa_con_contexto(
        minutos,
        fecha_hora_ingreso=fecha_hora_ingreso,
        fecha_hora_salida=fecha_hora_salida,
        contexto=obtener_contexto_tarifa(),
        devolver_flag=devolver_flag,
    )


def describir_detalle_tarifa(minutos, contexto=None):
    """
    Devuelve una descripción legible del tramo/modo cobrado para mostrar en ticket.

    No calcula montos; solo explica qué tramo aplicó para evitar tickets genéricos
    como "Modo personalizado" cuando el cliente necesita ver el tramo cobrado.
    """
    contexto = contexto or obtener_contexto_tarifa()
    config = contexto["config"]
    modo = config.get("modo_cobro", "minuto")

    if modo != "personalizado":
        return {
            "minuto": "Modo minuto",
            "auto": "Modo automático",
        }.get(modo, f"Modo {modo}")

    tramos = list(contexto.get("tramos") or [])
    if not tramos:
        return "Modo personalizado sin tramos"

    ultimo_tramo = tramos[-1]
    duracion_ciclo = ultimo_tramo["minuto_fin"] + 1
    horas_completas = minutos // duracion_ciclo
    minutos_restantes = minutos % duracion_ciclo

    tramo_aplicado = ultimo_tramo
    for tramo in tramos:
        if tramo["minuto_inicio"] <= minutos_restantes <= tramo["minuto_fin"]:
            tramo_aplicado = tramo
            break

    detalle = (
        "Modo personalizado - tramo "
        f"{tramo_aplicado['minuto_inicio']}-{tramo_aplicado['minuto_fin']} min"
    )
    if horas_completas:
        detalle += f" (+{horas_completas} ciclo(s) completo(s))"
    return detalle


def calcular_tarifa_con_contexto(
    minutos,
    fecha_hora_ingreso=None,
    fecha_hora_salida=None,
    contexto=None,
    devolver_flag=False,
):
    """
    Calcula la tarifa usando configuración/subida/tramos precargados.

    Mantiene la misma lógica de calcular_tarifa(), pero permite reutilizar el
    contexto cuando se calculan muchas tarifas en lote.
    """
    contexto = contexto or obtener_contexto_tarifa()
    config = contexto["config"]
    subida = contexto.get("subida")
    tramos_precargados = contexto.get("tramos") or []

    modo = config.get("modo_cobro", "minuto")
    tarifa_minima = int(config.get("tarifa_minima", 300))
    tarifa_hora = int(config.get("tarifa_hora", 1300))
    valor_minuto = int(config.get("valor_minuto", 25))

    total = 0
    subida_aplicada = False
    monto_extra_aplicado = 0

    # =========================================================
    # MODO MINUTO
    # =========================================================
    if modo == "minuto":
        if minutos <= 0:
            total = tarifa_minima
        else:
            total = tarifa_minima + (max(minutos - 1, 0) * valor_minuto)

        # Aplicar subida temporal proporcional por minutos si corresponde
        if subida and fecha_hora_ingreso and fecha_hora_salida:
            minutos_extra = calcular_minutos_en_subida(
                fecha_hora_ingreso,
                fecha_hora_salida,
                str(subida["hora_inicio"])[:5],
                str(subida["hora_fin"])[:5],
            )
            if minutos_extra > 0:
                subida_aplicada = True
                monto_extra_aplicado = minutos_extra * int(subida["monto_adicional"])
                total += monto_extra_aplicado

    # =========================================================
    # MODO PERSONALIZADO
    # =========================================================
    elif modo == "personalizado":
        tramos = list(tramos_precargados)

        subida_vigente = False
        monto_subida = 0

        if subida and fecha_hora_salida:
            hora_actual = fecha_hora_salida
            hora_inicio_str = str(subida["hora_inicio"])[:8]
            hora_fin_str = str(subida["hora_fin"])[:8]

            h_inicio_time = datetime.strptime(hora_inicio_str, "%H:%M:%S").time()
            h_fin_time = datetime.strptime(hora_fin_str, "%H:%M:%S").time()

            h_inicio = datetime.combine(hora_actual.date(), h_inicio_time)
            h_fin = datetime.combine(hora_actual.date(), h_fin_time)

            if h_fin <= h_inicio:
                from datetime import timedelta
                h_fin += timedelta(days=1)

            if h_inicio <= hora_actual <= h_fin:
                subida_vigente = True
                monto_subida = int(subida["monto_adicional"])

        if subida_vigente:
            subida_aplicada = True
            monto_extra_aplicado = monto_subida
            tramos = [{**tramo, "valor": tramo["valor"] + monto_subida} for tramo in tramos]

        if tramos:
            ultimo_tramo = tramos[-1]
            duracion_ciclo = ultimo_tramo["minuto_fin"] + 1
            horas_completas = minutos // duracion_ciclo
            minutos_restantes = minutos % duracion_ciclo

            total = horas_completas * tramos[-1]["valor"]

            for tramo in tramos:
                if tramo["minuto_inicio"] <= minutos_restantes <= tramo["minuto_fin"]:
                    total += tramo["valor"]
                    break
            else:
                total += tramos[-1]["valor"]
        else:
            total = tarifa_minima

    # =========================================================
    # MODO AUTO
    # =========================================================
    elif modo == "auto":
        bloques = (minutos // 60) + (1 if minutos % 60 > 0 else 0)
        total = tarifa_minima + ((max(bloques - 1, 0)) * tarifa_minima)

        if subida and fecha_hora_ingreso and fecha_hora_salida:
            minutos_extra = calcular_minutos_en_subida(
                fecha_hora_ingreso,
                fecha_hora_salida,
                str(subida["hora_inicio"])[:5],
                str(subida["hora_fin"])[:5],
            )
            if minutos_extra > 0:
                subida_aplicada = True
                monto_extra_aplicado = (minutos_extra // 5) * int(subida["monto_adicional"])
                total += monto_extra_aplicado

    else:
        total = tarifa_minima

    total = round(total)

    if devolver_flag:
        return total, subida_aplicada, monto_extra_aplicado
    return total

def construir_valores_automaticos(tarifa_min, tarifa_hora):
    """
    Construye la lista de valores en saltos de $100 entre la tarifa mínima
    y la tarifa por hora, incluyendo ambos extremos.

    Args:
        tarifa_min (int): Tarifa mínima.
        tarifa_hora (int): Tarifa por hora.

    Returns:
        list[int]: Lista de valores para los tramos.
    """
    if tarifa_min <= 0 or tarifa_hora <= 0:
        raise ValueError("Las tarifas deben ser mayores que cero.")

    if tarifa_hora < tarifa_min:
        raise ValueError("La tarifa por hora no puede ser menor que la tarifa mínima.")

    diferencia = tarifa_hora - tarifa_min

    if diferencia % 100 != 0:
        raise ValueError(
            "La diferencia entre la tarifa mínima y la tarifa por hora "
            "debe ser múltiplo de 100 para generar tramos automáticos."
        )

    valores = []
    valor = tarifa_min

    while valor <= tarifa_hora:
        valores.append(valor)
        valor += 100

    return valores

def construir_intervalos_equitativos(cantidad_tramos, minutos_totales=60):
    """
    Divide un total de minutos en una cantidad de tramos de forma lo más
    equitativa posible.

    Args:
        cantidad_tramos (int): Número de tramos a generar.
        minutos_totales (int): Minutos totales a repartir.

    Returns:
        list[tuple[int, int]]: Lista de intervalos (inicio, fin).
    """
    if cantidad_tramos <= 0:
        raise ValueError("La cantidad de tramos debe ser mayor que cero.")

    if cantidad_tramos > minutos_totales:
        raise ValueError(
            "No es posible generar más tramos que minutos disponibles dentro de una hora."
        )

    base = minutos_totales // cantidad_tramos
    sobrantes = minutos_totales % cantidad_tramos

    intervalos = []
    minuto_actual = 0

    for i in range(cantidad_tramos):
        longitud = base + (1 if i < sobrantes else 0)
        inicio = minuto_actual
        fin = minuto_actual + longitud - 1
        intervalos.append((inicio, fin))
        minuto_actual += longitud

    return intervalos

def generar_tramos_automaticos():
    """
    Genera tramos automáticos dentro de una hora, distribuyendo
    equitativamente los minutos según la cantidad de saltos de $100
    necesarios entre la tarifa mínima y la tarifa por hora.

    Ejemplo:
    - tarifa mínima = 300
    - tarifa hora = 1600
    - valores generados: 300, 400, 500, ..., 1600
    - esos valores se reparten equitativamente entre 0 y 59 minutos

    Returns:
        dict: Resultado de la operación.
    """
    config = obtener_configuracion()
    tarifa_min = int(config.get("tarifa_minima", 300))
    tarifa_hora = int(config.get("tarifa_hora", 1300))

    valores = construir_valores_automaticos(tarifa_min, tarifa_hora)
    intervalos = construir_intervalos_equitativos(len(valores), 60)

    tramos = []
    for (inicio, fin), valor in zip(intervalos, valores):
        tramos.append((inicio, fin, valor))

    with db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM tarifas_personalizadas")

        for inicio, fin, valor in tramos:
            cursor.execute("""
                INSERT INTO tarifas_personalizadas (minuto_inicio, minuto_fin, valor)
                VALUES (%s, %s, %s)
            """, (inicio, fin, valor))

    return {
        "ok": True,
        "tramos_generados": len(tramos),
        "mensaje": (
            f"Se generaron {len(tramos)} tramos automáticos "
            "distribuidos equitativamente entre 0 y 59 minutos."
        )
    }

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
    with db_cursor(dictionary=True) as cursor:
        if id_excluir:
            cursor.execute("""
                SELECT minuto_inicio, minuto_fin FROM tarifas_personalizadas
                WHERE id_tarifa != %s
            """, (id_excluir,))
        else:
            cursor.execute("SELECT minuto_inicio, minuto_fin FROM tarifas_personalizadas")

        tramos = cursor.fetchall()

    for tramo in tramos:
        if not (min_fin < tramo["minuto_inicio"] or min_inicio > tramo["minuto_fin"]):
            return False  # Hay superposición

    return True
