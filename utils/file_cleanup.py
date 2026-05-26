"""
Limpieza periódica y conservadora de archivos generados por la aplicación.
"""

from datetime import date, datetime, timedelta
from pathlib import Path

from controllers.config_controller import actualizar_configuracion, obtener_configuracion


CARPETAS_GENERADAS = ("tickets", "reportes", "cierres", "pdfs", "asistencias")


def _es_archivo_borrable(path):
    return path.is_file() and path.name not in {".gitkeep", ".gitignore"}


def limpiar_archivos_generados(dias_conservar=30, base_path=None):
    """
    Elimina archivos generados más antiguos que la ventana configurada.
    """
    base = Path(base_path or ".").resolve()
    limite = datetime.now() - timedelta(days=max(int(dias_conservar), 1))
    eliminados = 0
    errores = []

    for carpeta in CARPETAS_GENERADAS:
        carpeta_path = (base / carpeta).resolve()
        if not carpeta_path.exists() or not carpeta_path.is_dir():
            continue

        if base not in carpeta_path.parents and carpeta_path != base:
            errores.append(f"Ruta fuera del proyecto ignorada: {carpeta_path}")
            continue

        for archivo in carpeta_path.rglob("*"):
            if not _es_archivo_borrable(archivo):
                continue

            try:
                modificado = datetime.fromtimestamp(archivo.stat().st_mtime)
                if modificado < limite:
                    archivo.unlink()
                    eliminados += 1
            except OSError as exc:
                errores.append(f"No se pudo eliminar {archivo}: {exc}")

    return {"eliminados": eliminados, "errores": errores}


def ejecutar_limpieza_periodica(base_path=None):
    """
    Ejecuta limpieza automática como máximo una vez por día.
    """
    config = obtener_configuracion()
    if config.get("limpieza_automatica_activa", "1") != "1":
        return {"ejecutada": False, "motivo": "desactivada", "eliminados": 0, "errores": []}

    hoy = date.today().isoformat()
    if config.get("ultima_limpieza_archivos") == hoy:
        return {"ejecutada": False, "motivo": "ya_ejecutada", "eliminados": 0, "errores": []}

    dias = int(config.get("dias_conservar_archivos", "30"))
    resultado = limpiar_archivos_generados(dias, base_path=base_path)
    actualizar_configuracion("ultima_limpieza_archivos", hoy)

    return {
        "ejecutada": True,
        "motivo": "ok",
        "eliminados": resultado["eliminados"],
        "errores": resultado["errores"],
    }
