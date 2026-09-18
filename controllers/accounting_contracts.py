CHARGED_WASH_ONLY_STATES = {"FINALIZADO_COBRADO"}


def build_accounting_summary(
    parking_movements, bathroom_uses, wash_only_operations, expenses=(), monthly_payments=(), night_charges=()
):
    """Build the accounting shape shared by cierres and reports.

    Parking totals already include parking-linked washes. Solo wash revenue is
    reported separately only when it was charged immediately.
    """
    total_recaudado = _sum_amount(parking_movements, "tarifa_aplicada")
    total_banos_monto = _sum_amount(bathroom_uses, "monto")
    charged_wash_only = [
        operation
        for operation in wash_only_operations
        if operation.get("estado") in CHARGED_WASH_ONLY_STATES
    ]
    total_lavados_solos_monto = _sum_amount(charged_wash_only, "valor_lavado_snapshot")
    total_mensualidades_monto = _sum_amount(monthly_payments, "monto_snapshot")
    total_noches_monto = _sum_amount(night_charges, "monto_snapshot")

    total_general = (
        total_recaudado
        + total_banos_monto
        + total_lavados_solos_monto
        + total_mensualidades_monto
        + total_noches_monto
    )
    total_gastos = _sum_amount(expenses, "monto")

    return {
        "total_recaudado": total_recaudado,
        "total_ingresos": len(parking_movements),
        "total_salidas": len(parking_movements),
        "total_banos": len(bathroom_uses),
        "total_banos_monto": total_banos_monto,
        "total_lavados_solos": len(charged_wash_only),
        "total_lavados_solos_monto": total_lavados_solos_monto,
        "total_mensualidades": len(monthly_payments),
        "total_mensualidades_monto": total_mensualidades_monto,
        "total_noches": len(night_charges),
        "total_noches_monto": total_noches_monto,
        "total_general": total_general,
        "total_gastos": total_gastos,
        "total_neto": total_general - total_gastos,
    }


def build_report_totals(
    items,
    wash_only_operations=(),
    monthly_payments=(),
    night_charges=(),
    bathroom_uses=(),
    expenses=(),
):
    vehicle_items = _items_by_type(items, "vehiculo", include_legacy=True)
    bathroom_items = _items_by_type(items, "bano")
    wash_items = _items_by_type(items, "lavado_solo")
    monthly_items = _items_by_type(items, "mensualidad")
    night_items = _items_by_type(items, "noche")
    expense_items = _items_by_type(items, "gasto")

    total_recaudado = _sum_amount(vehicle_items, "tarifa_aplicada")
    total_banos_monto = _sum_category_amount(
        bathroom_items,
        bathroom_uses,
        item_key="tarifa_aplicada",
        source_key="monto",
    )
    total_lavados_solos_monto = _sum_wash_report_amount(wash_items, wash_only_operations)
    total_mensualidades_monto = _sum_category_amount(
        monthly_items,
        monthly_payments,
        item_key="tarifa_aplicada",
        source_key="monto_snapshot",
    )
    total_noches_monto = _sum_category_amount(
        night_items,
        night_charges,
        item_key="tarifa_aplicada",
        source_key="monto_snapshot",
    )
    total_gastos = _sum_expense_report_amount(expense_items, expenses)
    total_general = (
        total_recaudado
        + total_banos_monto
        + total_lavados_solos_monto
        + total_mensualidades_monto
        + total_noches_monto
    )

    return {
        "total_recaudado": total_recaudado,
        "total_movimientos": len(items),
        "total_banos": _category_count(bathroom_items, bathroom_uses),
        "total_banos_monto": total_banos_monto,
        "total_lavados_solos": _wash_report_count(wash_items, wash_only_operations),
        "total_lavados_solos_monto": total_lavados_solos_monto,
        "total_mensualidades": _category_count(monthly_items, monthly_payments),
        "total_mensualidades_monto": total_mensualidades_monto,
        "total_noches": _category_count(night_items, night_charges),
        "total_noches_monto": total_noches_monto,
        "total_gastos": total_gastos,
        "total_general": total_general,
        "total_neto": total_general - total_gastos,
    }


def _sum_amount(rows, key):
    return sum(int(row.get(key) or 0) for row in rows)


def _items_by_type(items, tipo, *, include_legacy=False):
    return [
        item
        for item in items
        if item.get("tipo") == tipo or (include_legacy and not item.get("tipo"))
    ]


def _category_count(items, source_rows):
    return len(items) if items else len(source_rows)


def _sum_category_amount(items, source_rows, *, item_key, source_key):
    if items:
        return _sum_amount(items, item_key)
    return _sum_amount(source_rows, source_key)


def _charged_wash_only(wash_only_operations):
    return [
        operation
        for operation in wash_only_operations
        if operation.get("estado") in CHARGED_WASH_ONLY_STATES
    ]


def _wash_report_count(items, wash_only_operations):
    return len(items) if items else len(_charged_wash_only(wash_only_operations))


def _sum_wash_report_amount(items, wash_only_operations):
    if items:
        return _sum_amount(items, "tarifa_aplicada")
    return _sum_amount(_charged_wash_only(wash_only_operations), "valor_lavado_snapshot")


def _sum_expense_report_amount(items, expenses):
    if items:
        return sum(abs(int(item.get("tarifa_aplicada") or 0)) for item in items)
    return _sum_amount(expenses, "monto")
