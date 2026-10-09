import os
import unittest
from datetime import datetime
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from views.reportes import ReportesWindow


class ReportesViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _crear_vista(self, api_token=None):
        with patch("views.reportes.obtener_patentes_conocidas", return_value=[]), \
             patch("views.reportes.obtener_usuarios", return_value=[]):
            return ReportesWindow(api_token=api_token)

    def _dashboard_card_titles(self, vista):
        return [card.layout().itemAt(0).widget().text() for card in vista.dashboard_metric_cards]

    def _api_closed_report_payload(self, closure_id="closure-2026-01"):
        return {
            "ok": True,
            "source": "api",
            "report_id": "closed-report-1",
            "period": {"from": "2026-01-01", "to": "2026-01-31", "state": "closed"},
            "closure_reference": {"id": closure_id, "closed_at": "2026-02-01T00:00:00Z"},
            "operation_totals": {"total_general": 12000, "total_gastos": 2000, "total_neto": 10000},
            "source_state": "canonical_snapshot",
            "catalog_version": "1.3.0",
            "historical_completeness": {"state": "complete", "reason": None},
            "capacity": {"total": 40, "occupied": 12, "available": 28},
            "warnings": [],
        }

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.obtener_resumen_dashboard_reportes")
    @patch("views.reportes.obtener_reportes")
    def test_muestra_resumen_canonico_api_sin_romper_tabla_local(self, reportes, dashboard, _messagebox):
        reportes.return_value = {
            "items": [
                {
                    "categoria": "Vehículo",
                    "patente": "ABC123",
                    "fecha_hora_ingreso": datetime(2026, 1, 10, 9, 0),
                    "fecha_hora_salida": datetime(2026, 1, 10, 10, 0),
                    "minutos": 60,
                    "tarifa_aplicada": 2500,
                    "usuario": "admin",
                }
            ],
            "totals": {"total_movimientos": 1, "total_general": 2500, "total_gastos": 0, "total_neto": 2500},
        }
        dashboard.return_value = {
            "source": "api",
            "catalog_version": "1.3.0",
            "period": {"id": "current", "state": "open"},
            "summary": [
                {"metric": "collected_sources_total", "label": "All collected sources", "value": 3000},
                {"metric": "operational_expense_total", "label": "Expenses", "value": 500},
                {"metric": "net_revenue_total", "label": "Net revenue", "value": 2500},
            ],
        }
        vista = self._crear_vista(api_token="desktop-token")

        vista.filtrar()

        self.assertIn("Fuente: API reporting", vista.label_dashboard_estado.text())
        self.assertIn("Versión catálogo: 1.3.0", vista.label_dashboard_estado.text())
        self.assertIn("Periodo: open", vista.label_dashboard_estado.text())
        self.assertIn("Fuente datos: api", vista.label_dashboard_estado.text())
        self.assertEqual(vista.label_dashboard_auditoria.text(), "Audit: not provided by reporting dashboard")
        self.assertEqual(self._dashboard_card_titles(vista)[:3], ["All collected sources", "Expenses", "Net revenue"])
        self.assertEqual([card.label_valor.text() for card in vista.dashboard_metric_cards[:3]], ["$3000", "$500", "$2500"])
        self.assertEqual(vista.tabla.rowCount(), 2)
        self.assertTrue(vista.boton_exportar.isEnabled())
        dashboard.assert_called_once()
        self.assertEqual(dashboard.call_args.kwargs["token"], "desktop-token")
        vista.close()

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.obtener_resumen_dashboard_reportes")
    @patch("views.reportes.obtener_reportes")
    def test_sin_token_muestra_resumen_local_y_no_rompe_pantalla(self, reportes, dashboard, _messagebox):
        reportes.return_value = {
            "items": [],
            "totals": {"total_movimientos": 0, "total_general": 0, "total_gastos": 0, "total_neto": 0},
        }
        dashboard.return_value = reportes.return_value
        vista = self._crear_vista()

        vista.filtrar()

        self.assertIn("Sin sesión API", vista.label_dashboard_estado.text())
        self.assertEqual([card.label_valor.text() for card in vista.dashboard_metric_cards[:3]], ["$0", "$0", "$0"])
        self.assertEqual(vista.tabla.rowCount(), 0)
        self.assertFalse(vista.boton_exportar.isEnabled())
        dashboard.assert_called_once()
        self.assertIsNone(dashboard.call_args.kwargs["token"])
        vista.close()

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.obtener_resumen_dashboard_reportes")
    @patch("views.reportes.obtener_reportes")
    def test_renderiza_estado_capacidad_y_advertencia_incompleta(self, reportes, dashboard, _messagebox):
        reportes.return_value = {
            "items": [
                {
                    "categoria": "Vehículo",
                    "patente": "ABC123",
                    "fecha_hora_ingreso": datetime(2026, 1, 10, 9, 0),
                    "fecha_hora_salida": datetime(2026, 1, 10, 10, 0),
                    "minutos": 60,
                    "tarifa_aplicada": 2500,
                    "usuario": "admin",
                }
            ],
            "totals": {"total_movimientos": 1, "total_general": 2500, "total_gastos": 0, "total_neto": 2500},
        }
        dashboard.return_value = {
            "source": "local_fallback",
            "source_state": "local_fallback",
            "period": {"id": "current", "state": "open"},
            "period_state": "open",
            "completeness": {"state": "incomplete", "reason": "API unavailable"},
            "capacity": None,
            "totals": reportes.return_value["totals"],
        }
        vista = self._crear_vista(api_token="desktop-token")

        vista.filtrar()

        self.assertIn("Periodo: open", vista.label_dashboard_estado.text())
        self.assertIn("Fuente datos: local_fallback", vista.label_dashboard_estado.text())
        self.assertIn("No oficial", vista.label_dashboard_estado.text())
        self.assertEqual(vista.label_dashboard_capacidad.text(), "Capacity: unavailable")
        self.assertIn("Audit: unavailable", vista.label_dashboard_auditoria.text())
        self.assertIn("local non-official fallback", vista.label_dashboard_auditoria.text())
        self.assertIn("API audit coverage unavailable", vista.label_dashboard_auditoria.text())
        self.assertIn("Incomplete totals", vista.label_dashboard_completitud.text())
        self.assertIn("API unavailable", vista.label_dashboard_completitud.text())
        self.assertIn("not official closure truth", vista.label_dashboard_advertencias.text())
        self.assertEqual([card.label_valor.text() for card in vista.dashboard_metric_cards[:3]], ["$2500", "$0", "$2500"])
        vista.close()

    def test_full_center_navigation_keeps_closed_exports_disabled_until_valid_api_report(self):
        vista = self._crear_vista(api_token="desktop-token")

        self.assertIn("Centro de Inteligencia", vista.label_centro_inteligencia.text())
        self.assertFalse(vista.boton_reportes_cerrados.isHidden())
        self.assertTrue(vista.boton_exportacion_canonica.isHidden())
        self.assertTrue(vista.boton_exportacion_canonica_xlsx.isHidden())
        self.assertFalse(vista.boton_exportacion_canonica.isEnabled())
        self.assertFalse(vista.boton_exportacion_canonica_xlsx.isEnabled())
        self.assertNotIn("CSV", vista.label_exportaciones_diferidas.text())
        vista.close()

    def test_capacity_state_is_rendered_with_historical_limitation(self):
        vista = self._crear_vista(api_token="desktop-token")

        capacity_text = vista._texto_capacidad_dashboard({"total": 50, "occupied": 10, "state": "historical-capacity-limited"})

        self.assertEqual(capacity_text, "Capacity: total 50, occupied 10, state historical-capacity-limited")
        vista.close()

    def test_dashboard_audit_label_renders_available_gap_unavailable_and_not_provided_states(self):
        vista = self._crear_vista(api_token="desktop-token")

        vista._actualizar_metadata_dashboard({
            "audit_coverage": {
                "state": "available",
                "available": ["operations", "closures"],
                "gaps": [],
                "unavailable": [],
                "notes": [],
            }
        })
        self.assertEqual(vista.label_dashboard_auditoria.text(), "Audit: available - operations, closures")

        vista._actualizar_metadata_dashboard({
            "audit_coverage": {
                "state": "gap",
                "available": ["operations"],
                "gaps": ["payments"],
                "unavailable": [],
                "notes": [],
            }
        })
        self.assertEqual(vista.label_dashboard_auditoria.text(), "Audit: gaps - payments; Available: operations")

        vista._actualizar_metadata_dashboard({
            "audit_coverage": {
                "state": "unavailable",
                "available": [],
                "gaps": [],
                "unavailable": ["prints"],
                "notes": ["Not integrated"],
            }
        })
        self.assertEqual(vista.label_dashboard_auditoria.text(), "Audit: unavailable - prints; Notes: Not integrated")

        vista._actualizar_metadata_dashboard({"audit_coverage": {"state": "not_provided"}})
        self.assertEqual(vista.label_dashboard_auditoria.text(), "Audit: not provided by reporting dashboard")
        vista.close()

    def test_audit_inventory_panel_renders_readiness_and_limitations(self):
        vista = self._crear_vista(api_token="desktop-token")

        vista._renderizar_inventario_auditoria({
            "ok": True,
            "source": "api",
            "source_state": "api",
            "period_id": "closure:42",
            "coverage": [
                {"source": "operations", "state": "available"},
                {"source": "payments", "state": "partial"},
                {"source": "legacy", "state": "unavailable"},
            ],
            "available_sources": ["operations"],
            "partial_sources": ["payments"],
            "unavailable_sources": ["legacy"],
            "affected_scopes": ["closures"],
            "unavailable_history": ["pre-1.3.0"],
            "requires_event_sourcing": False,
            "supports_persisted_anomalies": False,
            "unsupported_behaviors": ["source totals"],
        })

        self.assertIn("Period: closure:42", vista.label_audit_inventory_estado.text())
        self.assertIn("operations", vista.label_audit_inventory_coverage.text())
        self.assertIn("payments", vista.label_audit_inventory_coverage.text())
        self.assertIn("legacy", vista.label_audit_inventory_coverage.text())
        self.assertIn("Affected scopes: closures", vista.label_audit_inventory_limitaciones.text())
        self.assertIn("Unavailable history: pre-1.3.0", vista.label_audit_inventory_limitaciones.text())
        self.assertIn("Event sourcing required: no", vista.label_audit_inventory_limitaciones.text())
        self.assertIn("Persisted anomalies supported: no", vista.label_audit_inventory_limitaciones.text())
        self.assertIn("Unsupported behaviors: source totals", vista.label_audit_inventory_limitaciones.text())
        vista.close()

    def test_audit_inventory_panel_renders_unavailable_and_error_states(self):
        vista = self._crear_vista(api_token="desktop-token")

        vista._renderizar_inventario_auditoria({
            "ok": False,
            "source": "api",
            "source_state": "unavailable",
            "period_id": None,
            "coverage": [],
            "api_error": "API_AUDIT_INVENTORY_UNAVAILABLE",
        })
        self.assertIn("Inventory unavailable", vista.label_audit_inventory_estado.text())
        self.assertIn("No API-supplied coverage", vista.label_audit_inventory_coverage.text())

        vista._renderizar_inventario_auditoria({
            "ok": False,
            "source": "api",
            "source_state": "api_error",
            "period_id": "current",
            "coverage": [],
            "api_error": "API_UNAVAILABLE",
        })
        self.assertIn("Inventory error: API_UNAVAILABLE", vista.label_audit_inventory_estado.text())
        self.assertIn("No local fallback coverage is used", vista.label_audit_inventory_limitaciones.text())
        vista.close()

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.obtener_inventario_auditoria", create=True)
    @patch("views.reportes.obtener_resumen_dashboard_reportes")
    @patch("views.reportes.obtener_reportes")
    def test_dashboard_refresh_loads_audit_inventory_without_breaking_existing_flow(
        self,
        reportes,
        dashboard,
        inventory,
        _messagebox,
    ):
        reportes.return_value = {
            "items": [
                {
                    "categoria": "Vehículo",
                    "patente": "ABC123",
                    "fecha_hora_ingreso": datetime(2026, 1, 10, 9, 0),
                    "fecha_hora_salida": datetime(2026, 1, 10, 10, 0),
                    "minutos": 60,
                    "tarifa_aplicada": 2500,
                    "usuario": "admin",
                }
            ],
            "totals": {"total_movimientos": 1, "total_general": 2500, "total_gastos": 0, "total_neto": 2500},
        }
        dashboard.return_value = {"source": "api", "summary": []}
        inventory.return_value = {
            "ok": True,
            "source": "api",
            "source_state": "api",
            "period_id": "current",
            "coverage": [{"source": "operations", "state": "available"}],
            "available_sources": ["operations"],
            "partial_sources": [],
            "unavailable_sources": [],
            "affected_scopes": [],
            "unavailable_history": [],
            "requires_event_sourcing": False,
            "supports_persisted_anomalies": False,
            "unsupported_behaviors": [],
        }
        vista = self._crear_vista(api_token="desktop-token")

        vista.filtrar()

        inventory.assert_called_once_with("desktop-token")
        self.assertEqual(vista.tabla.rowCount(), 2)
        self.assertIn("operations", vista.label_audit_inventory_coverage.text())
        self.assertTrue(vista.boton_exportar.isEnabled())
        vista.close()

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.QInputDialog.getText", return_value=("closure-2026-01", True))
    @patch("views.reportes.obtener_operaciones_reporte_cerrado", create=True)
    @patch("views.reportes.obtener_reporte_cerrado", create=True)
    def test_loads_api_closed_report_and_renders_metadata_without_local_fallback(self, cerrado, operations, _input, information):
        cerrado.return_value = {
            "ok": True,
            "source": "api",
            "report_id": "closed-report-1",
            "period": {"from": "2026-01-01", "to": "2026-01-31", "state": "closed"},
            "closure_reference": {"id": "closure-2026-01", "closed_at": "2026-02-01T00:00:00Z"},
            "operation_totals": {"total_general": 12000, "total_gastos": 2000, "total_neto": 10000},
            "source_state": "canonical_snapshot",
            "catalog_version": "1.3.0",
            "historical_completeness": {"state": "complete", "reason": None},
            "capacity": {"total": 40, "occupied": 12, "available": 28},
            "warnings": [],
        }
        operations.return_value = {"ok": True, "rows": [], "pagination": {"limit": 25, "offset": 0, "total": 0}, "warnings": []}
        vista = self._crear_vista(api_token="desktop-token")

        self.assertNotIn("Future", vista.boton_reportes_cerrados.text())
        self.assertTrue(vista.boton_exportacion_canonica.isHidden())
        self.assertTrue(vista.boton_exportacion_canonica_xlsx.isHidden())

        vista.boton_reportes_cerrados.click()

        cerrado.assert_called_once_with("desktop-token", "closure-2026-01")
        operations.assert_called_once()
        self.assertEqual(vista.reporte_cerrado_actual["report_id"], "closed-report-1")
        self.assertIn("closed-report-1", vista.label_reporte_cerrado_estado.text())
        self.assertIn("closure-2026-01", vista.label_reporte_cerrado_periodo.text())
        self.assertIn("canonical_snapshot", vista.label_reporte_cerrado_fuente.text())
        self.assertIn("Completeness: complete", vista.label_reporte_cerrado_completitud.text())
        self.assertIn("Capacity: total 40", vista.label_reporte_cerrado_capacidad.text())
        self.assertEqual([card.label_valor.text() for card in vista.reporte_cerrado_metric_cards], ["$12000", "$2000", "$10000"])
        self.assertFalse(vista.boton_exportacion_canonica.isHidden())
        self.assertFalse(vista.boton_exportacion_canonica_xlsx.isHidden())
        self.assertTrue(vista.boton_exportacion_canonica.isEnabled())
        self.assertTrue(vista.boton_exportacion_canonica_xlsx.isEnabled())
        information.assert_called_once()
        self.assertIn("Closed report loaded", information.call_args.args[2])
        vista.close()

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.QInputDialog.getText", return_value=("42", True))
    @patch("views.reportes.obtener_operaciones_reporte_cerrado", create=True)
    @patch("views.reportes.obtener_reporte_cerrado", create=True)
    def test_closed_report_operation_rows_render_core_fields(self, cerrado, operations, _input, _information):
        cerrado.return_value = {
            "ok": True,
            "source": "api",
            "report_id": "closed-42",
            "period": {"from": "2026-01-01", "to": "2026-01-31"},
            "closure_reference": {"id": 42},
            "operation_totals": {},
            "warnings": [],
        }
        operations.return_value = {
            "ok": True,
            "rows": [
                {"category": "vehiculo", "amount": 2500, "operator": "admin", "plate": "ABC123", "timestamp": "2026-01-10T10:00:00"}
            ],
            "pagination": {"limit": 25, "offset": 0, "total": 1},
            "warnings": [],
        }
        vista = self._crear_vista(api_token="desktop-token")

        vista.boton_reportes_cerrados.click()

        self.assertEqual(vista.tabla_operaciones_reporte.rowCount(), 1)
        self.assertEqual(vista.tabla_operaciones_reporte.item(0, 0).text(), "vehiculo")
        self.assertEqual(vista.tabla_operaciones_reporte.item(0, 1).text(), "$2500")
        self.assertEqual(vista.tabla_operaciones_reporte.item(0, 2).text(), "admin")
        self.assertEqual(vista.tabla_operaciones_reporte.item(0, 3).text(), "ABC123")
        self.assertEqual(vista.tabla_operaciones_reporte.item(0, 4).text(), "2026-01-10T10:00:00")
        self.assertIn("1 of 1", vista.label_operaciones_paginacion.text())
        vista.close()

    @patch("views.reportes.obtener_operaciones_reporte_cerrado", create=True)
    def test_closed_report_operation_controls_send_filters_sort_and_pagination(self, operations):
        operations.return_value = {"ok": True, "rows": [], "pagination": {"limit": 10, "offset": 10, "total": 35}, "warnings": []}
        vista = self._crear_vista(api_token="desktop-token")
        vista.reporte_cerrado_actual = {"closure_reference": {"id": 42}}
        vista.input_operacion_categoria.setText("vehiculo")
        vista.input_operacion_operador.setText("admin")
        vista.input_operacion_patente.setText("ABC123")
        vista.combo_operacion_orden.setCurrentText("timestamp")
        vista.combo_operacion_direccion.setCurrentText("desc")
        vista.combo_operacion_limite.setCurrentText("10")
        vista.operaciones_offset = 10

        vista.cargar_operaciones_reporte_cerrado()

        operations.assert_called_once_with(
            "desktop-token",
            42,
            category="vehiculo",
            operator="admin",
            plate="ABC123",
            sort="timestamp",
            direction="desc",
            limit=10,
            offset=10,
        )
        self.assertIn("11-20 of 35", vista.label_operaciones_paginacion.text())
        self.assertTrue(vista.boton_operaciones_anterior.isEnabled())
        self.assertTrue(vista.boton_operaciones_siguiente.isEnabled())
        vista.close()

    @patch("views.reportes.obtener_operaciones_reporte_cerrado", create=True)
    def test_closed_report_operation_empty_warning_and_error_states_do_not_enable_exports(self, operations):
        vista = self._crear_vista(api_token="desktop-token")
        vista.reporte_cerrado_actual = {"closure_reference": {"id": 42}}
        operations.return_value = {
            "ok": True,
            "rows": [],
            "pagination": {"limit": 25, "offset": 0, "total": 0},
            "warnings": ["No operation rows available"],
        }

        vista.cargar_operaciones_reporte_cerrado()

        self.assertEqual(vista.tabla_operaciones_reporte.rowCount(), 0)
        self.assertIn("No operations found", vista.label_operaciones_estado.text())
        self.assertIn("No operation rows available", vista.label_operaciones_advertencias.text())
        self.assertTrue(vista.boton_exportacion_canonica.isHidden())
        self.assertTrue(vista.boton_exportacion_canonica_xlsx.isHidden())

        operations.return_value = {"ok": False, "api_error": "API_UNAVAILABLE", "status": 503, "rows": []}
        vista.cargar_operaciones_reporte_cerrado()

        self.assertIn("API_UNAVAILABLE", vista.label_operaciones_estado.text())
        self.assertEqual(vista.tabla_operaciones_reporte.rowCount(), 0)
        self.assertTrue(vista.boton_exportacion_canonica.isHidden())
        vista.close()

    def test_local_calendar_reports_remain_legacy_local_and_separate_from_closed_operations(self):
        vista = self._crear_vista(api_token="desktop-token")

        self.assertIn("legacy/local", vista.label_reportes_locales_legacy.text())
        self.assertEqual(vista.tabla.columnCount(), 7)
        self.assertEqual(vista.tabla_operaciones_reporte.columnCount(), 5)
        self.assertTrue(vista.boton_exportacion_canonica.isHidden())
        self.assertFalse(vista.boton_exportacion_canonica.isEnabled())
        vista.resultados = {"items": [{"patente": "ABC123"}], "totals": {}}
        vista.reporte_cerrado_actual = {"source": "local", "closure_reference": {"id": "fabricated"}}
        vista._actualizar_estado_exportaciones_cerradas()
        self.assertTrue(vista.boton_exportacion_canonica.isHidden())
        self.assertTrue(vista.boton_exportacion_canonica_xlsx.isHidden())
        vista.close()

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.QMessageBox.warning")
    @patch("views.reportes.QInputDialog.getText", return_value=("closure-2026-02", True))
    @patch("views.reportes.obtener_reporte_cerrado", create=True)
    def test_closed_report_warnings_and_api_errors_are_actionable(self, cerrado, _input, warning, _information):
        cerrado.return_value = {
            "ok": True,
            "source": "api",
            "report_id": "closed-report-2",
            "period": {"from": "2026-02-01", "to": "2026-02-28"},
            "closure_reference": {"id": "closure-2026-02"},
            "operation_totals": {"total_general": 7000, "total_gastos": 1000, "total_neto": 6000},
            "source_state": "partial_snapshot",
            "historical_completeness": {"state": "incomplete", "reason": "Backfill pending"},
            "warnings": ["Missing legacy rows"],
        }
        vista = self._crear_vista(api_token="desktop-token")

        vista.boton_reportes_cerrados.click()

        self.assertIn("Incomplete totals", vista.label_reporte_cerrado_completitud.text())
        self.assertIn("Backfill pending", vista.label_reporte_cerrado_completitud.text())
        self.assertIn("Missing legacy rows", vista.label_reporte_cerrado_advertencias.text())

        cerrado.return_value = {
            "ok": False,
            "api_error": "Closed report not found",
            "status": 404,
            "source_state": "api_error",
        }
        vista.boton_reportes_cerrados.click()

        warning.assert_called_once()
        self.assertIn("Closed report not found", warning.call_args.args[2])
        self.assertIn("Closed report not found", vista.label_reporte_cerrado_advertencias.text())
        self.assertEqual(vista.card_reporte_cerrado_neto.label_valor.text(), "$6000")
        vista.close()

    def test_api_payload_without_closure_reference_keeps_closed_exports_disabled(self):
        vista = self._crear_vista(api_token="desktop-token")

        vista.reporte_cerrado_actual = {"ok": True, "source": "api", "closure_reference": {}}
        vista._renderizar_reporte_cerrado(vista.reporte_cerrado_actual)

        self.assertTrue(vista.boton_exportacion_canonica.isHidden())
        self.assertTrue(vista.boton_exportacion_canonica_xlsx.isHidden())
        self.assertFalse(vista.boton_exportacion_canonica.isEnabled())
        self.assertFalse(vista.boton_exportacion_canonica_xlsx.isEnabled())
        vista.close()

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.exportar_reporte_cerrado", create=True)
    def test_closed_report_pdf_and_xlsx_clicks_use_loaded_closure_id(self, exportar, _information):
        exportar.return_value = {"ok": True, "format": "pdf", "path": "reportes/closed_closure-2026-01.pdf"}
        vista = self._crear_vista(api_token="desktop-token")
        vista.reporte_cerrado_actual = self._api_closed_report_payload()
        vista._renderizar_reporte_cerrado(vista.reporte_cerrado_actual)

        vista.boton_exportacion_canonica.click()
        exportar.return_value = {"ok": True, "format": "xlsx", "path": "reportes/closed_closure-2026-01.xlsx"}
        vista.boton_exportacion_canonica_xlsx.click()

        self.assertEqual(exportar.call_args_list[0].args, ("desktop-token", "closure-2026-01", "pdf"))
        self.assertEqual(exportar.call_args_list[1].args, ("desktop-token", "closure-2026-01", "xlsx"))
        self.assertIn("reportes/closed_closure-2026-01.xlsx", vista.label_exportaciones_diferidas.text())
        vista.close()

    @patch("views.reportes.QMessageBox.warning")
    @patch("views.reportes.exportar_reporte_cerrado", create=True)
    def test_closed_report_export_error_is_actionable_and_preserves_retry_state(self, exportar, warning):
        exportar.return_value = {"ok": False, "format": "pdf", "status": 500, "api_error": "EXPORT_FAILED"}
        vista = self._crear_vista(api_token="desktop-token")
        vista.reporte_cerrado_actual = self._api_closed_report_payload()
        vista._renderizar_reporte_cerrado(vista.reporte_cerrado_actual)

        vista.boton_exportacion_canonica.click()

        self.assertEqual(vista.reporte_cerrado_actual["closure_reference"]["id"], "closure-2026-01")
        self.assertFalse(vista.boton_exportacion_canonica.isHidden())
        self.assertTrue(vista.boton_exportacion_canonica.isEnabled())
        self.assertIn("EXPORT_FAILED", vista.label_exportaciones_diferidas.text())
        self.assertIn("status 500", vista.label_exportaciones_diferidas.text())
        self.assertIn("EXPORT_FAILED", warning.call_args.args[2])
        vista.close()


if __name__ == "__main__":
    unittest.main()
