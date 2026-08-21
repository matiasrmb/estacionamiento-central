from PySide6.QtCore import QSettings


METRICS_PRIVACY_MODE_KEY = "metricas/modo_privacidad"


def obtener_modo_privacidad_metricas():
    """Retorna la preferencia local de ocultar valores en tarjetas métricas."""
    settings = QSettings("Estacionamiento Central", "Estacionamiento Central")
    return settings.value(METRICS_PRIVACY_MODE_KEY, False, type=bool)


def guardar_modo_privacidad_metricas(activo):
    """Guarda la preferencia solo para este equipo de escritorio."""
    settings = QSettings("Estacionamiento Central", "Estacionamiento Central")
    settings.setValue(METRICS_PRIVACY_MODE_KEY, bool(activo))
