def build_ticket_detail_lines(detalle_secciones):
    if not detalle_secciones:
        return []

    lines = []
    total = 0
    for key, title in (("lavado", "Lavado"), ("estadia", "Estadia")):
        section = detalle_secciones.get(key)
        if not section:
            continue
        monto = int(section.get("monto") or 0)
        total += monto
        lines.extend([
            f"{title}:",
            f"Inicio: {_format_ticket_datetime(section.get('inicio'))}",
            f"Fin: {_format_ticket_datetime(section.get('fin'))}",
            f"Duracion: {int(section.get('duracion_minutos') or 0)} min",
            f"Monto: ${monto:.0f}",
        ])

    if lines and "lavado" in detalle_secciones and "estadia" in detalle_secciones:
        lines.append(f"Total detalle: ${total:.0f}")
    return lines


def _format_ticket_datetime(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d-%m-%Y %H:%M:%S")
    return str(value or "-")
