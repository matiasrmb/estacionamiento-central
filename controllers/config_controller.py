"""
Controlador para la gestión de configuración general del sistema.

Incluye funciones para obtener y actualizar parámetros como tarifas, modos de cobro, etc.
"""

from utils.db import db_cursor


LAVADO_CATEGORIAS = [
    ("lavado_citycar", "CityCar", "5000"),
    ("lavado_suv", "SUV", "8000"),
    ("lavado_camioneta", "Camioneta", "10000"),
    ("lavado_furgon", "Furgón", "15000"),
    ("lavado_minibus", "Mini bus o vehículos grandes", "25000"),
]

PC_PRINT_JOBS_ACTIVOS_KEY = "pc_print_jobs_activos"

def obtener_configuracion():
    """
    Obtiene la configuración general del sistema como un diccionario clave-valor.

    Returns:
        dict: Configuración del sistema.
    """
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("SELECT clave, valor FROM configuracion")
        datos = cursor.fetchall()

    return {item["clave"]: item["valor"] for item in datos}

def actualizar_configuracion(clave, valor):
    """
    Actualiza una clave de configuración específica.

    Args:
        clave (str): Nombre de la clave.
        valor (str/int): Valor a asignar.

    Returns:
        bool: True si se actualizó correctamente.
    """
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO configuracion (clave, valor)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE valor = VALUES(valor)
            """,
            (clave, str(valor))
        )
    return True

def guardar_configuracion_masiva(diccionario_config):
    """
    Actualiza múltiples claves de configuración en una sola operación.

    Args:
        diccionario_config (dict): Diccionario clave-valor con los cambios.
    """
    with db_cursor(commit=True) as cursor:
        for clave, valor in diccionario_config.items():
            cursor.execute(
                """
                INSERT INTO configuracion (clave, valor)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE valor = VALUES(valor)
                """,
                (clave, str(valor))
            )


def print_jobs_pc_activos(configuracion=None):
    """Indica si las operaciones deben crear trabajos durables para PC."""
    config = configuracion if configuracion is not None else obtener_configuracion()
    return config.get(PC_PRINT_JOBS_ACTIVOS_KEY, "1") != "0"


def obtener_print_jobs_pc_activos(cursor):
    """Lee la opción de impresión desde la transacción operativa actual."""
    try:
        cursor.execute(
            "SELECT valor FROM configuracion WHERE clave = %s LIMIT 1",
            (PC_PRINT_JOBS_ACTIVOS_KEY,),
        )
        fila = cursor.fetchone()
    except Exception:
        return True

    if not fila:
        return True
    valor = fila["valor"] if isinstance(fila, dict) else fila[0]
    return str(valor) != "0"


def obtener_valores_lavado(configuracion=None):
    """
    Retorna los valores de lavado configurados por categoría.

    Args:
        configuracion (dict | None): Configuración ya cargada, para evitar
            consultas repetidas desde la UI o lógica de negocio.

    Returns:
        dict: clave -> {label, valor}
    """
    config = configuracion or obtener_configuracion()
    return {
        clave: {
            "label": label,
            "valor": int(config.get(clave, valor_default)),
        }
        for clave, label, valor_default in LAVADO_CATEGORIAS
    }
