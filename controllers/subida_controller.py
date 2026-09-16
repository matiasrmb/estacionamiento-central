from utils.db import db_cursor
from datetime import datetime, time, timedelta


def _time_as_hhmm(value):
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds()) % (24 * 60 * 60)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02}:{minutes:02}"
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")
    parts = str(value).split(":")
    if len(parts) >= 2:
        return f"{int(parts[0]):02}:{int(parts[1]):02}"
    return str(value)[:5]


def materializar_ventana_subida(referencia, hora_inicio_str, hora_fin_str):
    hora_inicio_time = datetime.strptime(_time_as_hhmm(hora_inicio_str), "%H:%M").time()
    hora_fin_time = datetime.strptime(_time_as_hhmm(hora_fin_str), "%H:%M").time()

    fecha_base = referencia.date()
    cruza_medianoche = hora_fin_time <= hora_inicio_time
    if cruza_medianoche and referencia.time() <= hora_fin_time:
        fecha_base -= timedelta(days=1)

    inicio = datetime.combine(fecha_base, hora_inicio_time)
    fin = datetime.combine(fecha_base, hora_fin_time)
    if cruza_medianoche:
        fin += timedelta(days=1)
    return inicio, fin

def crear_subida_temporal(hora_inicio, hora_fin, monto_adicional):
    """
    Crea una nueva subida de precios temporal y desactiva la anterior.

    Args:
        hora_inicio (str): Hora de inicio en formato "HH:MM".
        hora_fin (str): Hora de fin en formato "HH:MM".
        monto_adicional (int): Monto adicional a aplicar.

    Returns:
        bool: True si se creó correctamente.
    """
    try:
        with db_cursor(commit=True) as cursor:
            # Desactivar anterior
            cursor.execute("UPDATE subida_precios SET activa = 0")

            # Insertar nueva
            cursor.execute("""
                INSERT INTO subida_precios (hora_inicio, hora_fin, monto_adicional, activa)
                VALUES (%s, %s, %s, 1)
            """, (hora_inicio, hora_fin, monto_adicional))

        return True
    except Exception as e:
        print(f"[ERROR] al crear subida temporal: {e}")
        return False

def obtener_subida_activa():
    """
    Obtiene la subida de precios temporal activa, si existe.

    Returns:
        dict or None: Subida activa con hora_inicio, hora_fin, monto_adicional.
    """
    try:
        with db_cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT * FROM subida_precios
                WHERE activa = 1
                ORDER BY id_subida DESC LIMIT 1
            """)
            subida = cursor.fetchone()
        return subida
    except Exception as e:
        print(f"[ERROR] al obtener subida activa: {e}")
        return None

def calcular_minutos_en_subida(fecha_hora_ingreso, fecha_hora_salida, hora_inicio_str, hora_fin_str):
    """
    Calcula cuántos minutos del periodo de ingreso/salida coinciden con la subida temporal.

    Returns:
        int: Minutos que se cruzan con la subida.
    """

    if fecha_hora_salida <= fecha_hora_ingreso:
        return 0

    ventanas = set()
    hora_inicio_time = datetime.strptime(_time_as_hhmm(hora_inicio_str), "%H:%M").time()
    hora_fin_time = datetime.strptime(_time_as_hhmm(hora_fin_str), "%H:%M").time()
    cruza_medianoche = hora_fin_time <= hora_inicio_time
    fecha = fecha_hora_ingreso.date() - timedelta(days=1)
    while fecha <= fecha_hora_salida.date():
        inicio = datetime.combine(fecha, hora_inicio_time)
        fin = datetime.combine(fecha, hora_fin_time)
        if cruza_medianoche:
            fin += timedelta(days=1)
        ventanas.add((inicio, fin))
        fecha += timedelta(days=1)

    minutos = 0
    for inicio_subida, fin_subida in ventanas:
        inicio_real = max(fecha_hora_ingreso, inicio_subida)
        fin_real = min(fecha_hora_salida, fin_subida)
        if inicio_real < fin_real:
            minutos += int((fin_real - inicio_real).total_seconds() / 60)
    return minutos
