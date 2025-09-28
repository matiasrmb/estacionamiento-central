from utils.db import get_connection
from datetime import datetime, time, timedelta

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
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Desactivar anterior
        cursor.execute("UPDATE subida_precios SET activa = 0")

        # Insertar nueva
        cursor.execute("""
            INSERT INTO subida_precios (hora_inicio, hora_fin, monto_adicional, activa)
            VALUES (%s, %s, %s, 1)
        """, (hora_inicio, hora_fin, monto_adicional))

        conn.commit()
        return True
    except Exception as e:
        print(f"[ERROR] al crear subida temporal: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def obtener_subida_activa():
    """
    Obtiene la subida de precios temporal activa, si existe.

    Returns:
        dict or None: Subida activa con hora_inicio, hora_fin, monto_adicional.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
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
    finally:
        cursor.close()
        conn.close()

def calcular_minutos_en_subida(fecha_hora_ingreso, fecha_hora_salida, hora_inicio_str, hora_fin_str):
    """
    Calcula cuántos minutos del periodo de ingreso/salida coinciden con la subida temporal.

    Returns:
        int: Minutos que se cruzan con la subida.
    """

    hora_inicio = datetime.combine(fecha_hora_ingreso.date(), datetime.strptime(hora_inicio_str, "%H:%M").time())
    hora_fin = datetime.combine(fecha_hora_ingreso.date(), datetime.strptime(hora_fin_str, "%H:%M").time())

    # Si la subida cruza de un día al siguiente (ej: 22:00 a 02:00)
    if hora_fin <= hora_inicio:
        hora_fin += timedelta(days=1)

    inicio_real = max(fecha_hora_ingreso, hora_inicio)
    fin_real = min(fecha_hora_salida, hora_fin)

    if inicio_real >= fin_real:
        return 0  # No hay cruce

    return int((fin_real - inicio_real).total_seconds() / 60)
