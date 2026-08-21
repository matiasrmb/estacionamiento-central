import re


_VALID_PLATE_PATTERN = re.compile(r"^(?:[A-Z]{4}[0-9]{2}|[A-Z]{3}[0-9]{2}|[A-Z]{2}[0-9]{3}[A-Z]{2}|[A-Z]{3}[0-9]{3}|[A-Z]{2}[0-9]{4})$")


def normalizar_patente(valor):
    """Mayúsculas y eliminación exclusiva de espacios y guiones."""
    return str(valor or "").upper().replace(" ", "").replace("-", "")


def validar_patente(valor):
    return bool(_VALID_PLATE_PATTERN.fullmatch(normalizar_patente(valor)))


def requerir_patente_valida(valor):
    patente = normalizar_patente(valor)
    if not _VALID_PLATE_PATTERN.fullmatch(patente):
        raise ValueError("INVALID_PLATE")
    return patente
