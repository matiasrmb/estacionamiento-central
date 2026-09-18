import unittest

from controllers.accounting_contracts import build_accounting_summary, build_report_totals


class AccountingReportContractsTests(unittest.TestCase):
    def test_parking_wash_revenue_stays_inside_parking_total(self):
        summary = build_accounting_summary(
            parking_movements=[{"tarifa_aplicada": 1200}],
            bathroom_uses=[{"monto": 300}],
            wash_only_operations=[],
        )

        self.assertEqual(summary["total_recaudado"], 1200)
        self.assertEqual(summary["total_lavados_solos"], 0)
        self.assertEqual(summary["total_lavados_solos_monto"], 0)
        self.assertEqual(summary["total_general"], 1500)

    def test_charge_now_wash_only_revenue_is_separate_and_in_total_general(self):
        summary = build_accounting_summary(
            parking_movements=[{"tarifa_aplicada": 1200}],
            bathroom_uses=[{"monto": 300}],
            wash_only_operations=[
                {"estado": "FINALIZADO_COBRADO", "valor_lavado_snapshot": 8000},
                {"estado": "ACTIVO", "valor_lavado_snapshot": 9000},
            ],
        )

        self.assertEqual(summary["total_recaudado"], 1200)
        self.assertEqual(summary["total_lavados_solos"], 1)
        self.assertEqual(summary["total_lavados_solos_monto"], 8000)
        self.assertEqual(summary["total_general"], 9500)

    def test_expenses_reduce_net_total_without_changing_gross_total(self):
        summary = build_accounting_summary(
            parking_movements=[{"tarifa_aplicada": 1000}],
            bathroom_uses=[{"monto": 300}],
            wash_only_operations=[],
            expenses=[{"monto": 450}],
        )

        self.assertEqual(summary["total_general"], 1300)
        self.assertEqual(summary["total_gastos"], 450)
        self.assertEqual(summary["total_neto"], 850)

    def test_monthly_payments_are_included_in_gross_and_net_totals(self):
        summary = build_accounting_summary(
            parking_movements=[{"tarifa_aplicada": 1000}],
            bathroom_uses=[],
            wash_only_operations=[],
            expenses=[{"monto": 300}],
            monthly_payments=[{"monto_snapshot": 50000}],
        )

        self.assertEqual(summary["total_mensualidades"], 1)
        self.assertEqual(summary["total_mensualidades_monto"], 50000)
        self.assertEqual(summary["total_general"], 51000)
        self.assertEqual(summary["total_neto"], 50700)

    def test_wash_then_stay_defers_wash_revenue_until_parking_exit(self):
        summary = build_accounting_summary(
            parking_movements=[{"tarifa_aplicada": 10000}],
            bathroom_uses=[],
            wash_only_operations=[
                {"estado": "COBRADO_EN_SALIDA", "valor_lavado_snapshot": 8000},
            ],
        )

        self.assertEqual(summary["total_recaudado"], 10000)
        self.assertEqual(summary["total_lavados_solos"], 0)
        self.assertEqual(summary["total_lavados_solos_monto"], 0)
        self.assertEqual(summary["total_general"], 10000)

    def test_report_totals_include_only_charge_now_solo_lavado(self):
        totals = build_report_totals(
            items=[{"tipo": "vehiculo", "tarifa_aplicada": 10000}],
            wash_only_operations=[
                {"estado": "FINALIZADO_COBRADO", "valor_lavado_snapshot": 8000},
                {"estado": "CONVERTIDO_ESTADIA", "valor_lavado_snapshot": 9000},
            ],
        )

        self.assertEqual(totals["total_recaudado"], 10000)
        self.assertEqual(totals["total_lavados_solos"], 1)
        self.assertEqual(totals["total_lavados_solos_monto"], 8000)
        self.assertEqual(totals["total_general"], 18000)

    def test_report_totals_include_monthly_payments_separately(self):
        totals = build_report_totals(
            items=[{"tipo": "vehiculo", "tarifa_aplicada": 1200}],
            wash_only_operations=[],
            monthly_payments=[{"monto_snapshot": 50000}],
        )

        self.assertEqual(totals["total_recaudado"], 1200)
        self.assertEqual(totals["total_mensualidades"], 1)
        self.assertEqual(totals["total_mensualidades_monto"], 50000)
        self.assertEqual(totals["total_general"], 51200)

    def test_prepaid_nights_are_separate_from_exit_revenue_and_in_gross_total(self):
        summary = build_accounting_summary(
            parking_movements=[{"tarifa_aplicada": 1200}],
            bathroom_uses=[],
            wash_only_operations=[],
            night_charges=[{"monto_snapshot": 5000}],
        )

        self.assertEqual(summary["total_recaudado"], 1200)
        self.assertEqual(summary["total_noches"], 1)
        self.assertEqual(summary["total_noches_monto"], 5000)
        self.assertEqual(summary["total_general"], 6200)

    def test_report_totals_include_all_accounting_categories_and_movement_count(self):
        totals = build_report_totals(
            items=[
                {"tipo": "vehiculo", "tarifa_aplicada": 10000},
                {"tipo": "bano", "tarifa_aplicada": 300},
                {"tipo": "lavado_solo", "tarifa_aplicada": 8000},
                {"tipo": "mensualidad", "tarifa_aplicada": 50000},
                {"tipo": "noche", "tarifa_aplicada": 5000},
                {"tipo": "gasto", "tarifa_aplicada": -2500},
            ],
            bathroom_uses=[{"monto": 300}],
            wash_only_operations=[
                {"estado": "FINALIZADO_COBRADO", "valor_lavado_snapshot": 8000},
                {"estado": "CONVERTIDO_ESTADIA", "valor_lavado_snapshot": 9000},
            ],
            monthly_payments=[{"monto_snapshot": 50000}],
            night_charges=[{"monto_snapshot": 5000}],
            expenses=[{"monto": 2500}],
        )

        self.assertEqual(totals["total_recaudado"], 10000)
        self.assertEqual(totals["total_banos"], 1)
        self.assertEqual(totals["total_banos_monto"], 300)
        self.assertEqual(totals["total_lavados_solos"], 1)
        self.assertEqual(totals["total_lavados_solos_monto"], 8000)
        self.assertEqual(totals["total_mensualidades"], 1)
        self.assertEqual(totals["total_mensualidades_monto"], 50000)
        self.assertEqual(totals["total_noches"], 1)
        self.assertEqual(totals["total_noches_monto"], 5000)
        self.assertEqual(totals["total_gastos"], 2500)
        self.assertEqual(totals["total_general"], 73300)
        self.assertEqual(totals["total_neto"], 70800)
        self.assertEqual(totals["total_movimientos"], 6)


if __name__ == "__main__":
    unittest.main()
