from controllers.config_controller import obtener_valores_lavado


def calcular_minutos_estadia_por_horarios(hora_ingreso, hora_salida):
    """Calcula minutos de estadía para una cotización entre dos horas HH:MM."""
    ingreso = _parse_hora_cotizacion(hora_ingreso, "hora de ingreso")
    salida = _parse_hora_cotizacion(hora_salida, "hora de salida")

    minutos_ingreso = ingreso[0] * 60 + ingreso[1]
    minutos_salida = salida[0] * 60 + salida[1]
    duracion = minutos_salida - minutos_ingreso

    if duracion == 0:
        raise ValueError("La hora de salida debe ser distinta a la hora de ingreso.")
    if duracion < 0:
        raise ValueError("La hora de salida debe ser posterior a la hora de ingreso.")
    return duracion


def cotizar_estadia(minutos, monto_estadia, tamano_vehiculo=None):
    return {
        "tipo": "estadia",
        "minutos": int(minutos),
        "monto": int(monto_estadia),
    }


def cotizar_lavado(tipo_lavado, monto_lavado):
    return {
        "tipo": "lavado",
        "tipo_lavado": tipo_lavado,
        "monto": int(monto_lavado),
    }


def cotizar_mensualidad(vehiculos):
    detalles = []
    total_mensual = 0
    total_diario = 0
    requiere_monto = False

    for vehiculo in vehiculos:
        monto = _resolver_monto_mensual(vehiculo)
        if monto is None:
            requiere_monto = True
            detalles.append({
                "patente": vehiculo.get("patente"),
                "monto_mensual": None,
                "costo_diario": None,
                "requiere_monto": True,
            })
            continue

        costo_diario = round(monto / 30)
        total_mensual += monto
        total_diario += costo_diario
        detalles.append({
            "patente": vehiculo.get("patente"),
            "monto_mensual": monto,
            "costo_diario": costo_diario,
            "requiere_monto": False,
        })

    return {
        "tipo": "mensualidad",
        "vehiculos": detalles,
        "total_mensual": total_mensual,
        "total_diario": total_diario,
        "requiere_monto": requiere_monto,
        "monto": total_mensual,
    }


def cotizar_combinada(*items):
    items_validos = [item for item in items if item]
    return {
        "tipo": "combinada",
        "items": items_validos,
        "total": sum(int(item.get("monto") or 0) for item in items_validos),
    }


def preview_cotizacion(payload):
    items = []

    estadia = payload.get("estadia") or {}
    if estadia:
        items.append(cotizar_estadia(
            estadia.get("minutos", 0),
            estadia.get("monto_estadia", 0),
            tamano_vehiculo=estadia.get("tamano_vehiculo"),
        ))

    lavado = payload.get("lavado") or {}
    if lavado:
        items.append(cotizar_lavado(
            lavado.get("tipo_lavado"),
            lavado.get("monto_lavado", 0),
        ))

    mensualidad = payload.get("mensualidad") or {}
    if mensualidad:
        preview_mensual = cotizar_mensualidad(mensualidad.get("vehiculos", []))
        if preview_mensual["requiere_monto"]:
            raise ValueError("MONTHLY_AMOUNT_REQUIRED")
        items.append(preview_mensual)

    preview = cotizar_combinada(*items)
    preview["creates_billable_rows"] = False
    return preview


def wash_quote_options_from_legacy_config(configuracion=None):
    opciones = []
    for clave, data in obtener_valores_lavado(configuracion).items():
        monto = _positive_int_or_none(data.get("valor"))
        if monto is None:
            continue
        opciones.append({
            "id_tipo_vehiculo_lavado": None,
            "codigo": clave,
            "nombre": data.get("label") or clave,
            "valor_lavado": monto,
            "activo": 1,
            "source": "legacy_configuracion",
        })
    return opciones


def resolve_wash_quote_options(new_table_items, configuracion=None):
    active_new_items = [
        dict(item) for item in (new_table_items or [])
        if int(item.get("activo") or 0)
    ]
    if active_new_items:
        return active_new_items
    return wash_quote_options_from_legacy_config(configuracion)


def _resolver_monto_mensual(vehiculo):
    for clave in ("monto_mensual", "monto_configurado", "monto_mensual_default"):
        monto = vehiculo.get(clave)
        if monto not in (None, "", 0, "0"):
            return int(monto)
    return None


def _positive_int_or_none(value):
    try:
        amount = int(float(value))
    except (TypeError, ValueError):
        return None
    return amount if amount > 0 else None


def _parse_hora_cotizacion(value, label):
    text = str(value or "").strip()
    parts = text.split(":")
    if len(parts) != 2:
        raise ValueError(f"Ingresá la {label} con formato HH:MM.")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError as exc:
        raise ValueError(f"Ingresá la {label} con formato HH:MM.") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Ingresá una {label} válida con formato HH:MM.")
    return hour, minute
