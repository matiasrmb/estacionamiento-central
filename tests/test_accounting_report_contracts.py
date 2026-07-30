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


if __name__ == "__main__":
    unittest.main()
