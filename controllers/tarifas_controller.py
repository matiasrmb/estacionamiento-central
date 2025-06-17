from utils.db import get_connection
from controllers.config_controller import obtener_configuracion

def obtener_tarifas_personalizadas():
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tarifas_personalizadas (minuto_inicio, minuto_fin, valor)
        VALUES (%s, %s, %s)
    """, (min_inicio, min_fin, valor))
    conn.commit()
    cursor.close()
    conn.close()

def eliminar_intervalo(id_tarifa):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tarifas_personalizadas WHERE id_tarifa = %s", (id_tarifa,))
    conn.commit()
    cursor.close()
    conn.close()

def actualizar_intervalo(id_tarifa, min_inicio, min_fin, valor):
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
    from controllers.config_controller import obtener_configuracion
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
