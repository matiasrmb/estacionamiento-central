import unittest

from utils.printer_diagnostics import build_printer_diagnostics


class PrinterDiagnosticsTests(unittest.TestCase):
    def test_reports_supported_path_when_configured_printer_exists(self):
        result = build_printer_diagnostics(
            sumatra_path=r"C:\EstacionamientoCentral\tools\SumatraPDF\SumatraPDF.exe",
            sumatra_exists=True,
            configured_printer="EPSON TM-T20III Receipt",
            installed_printers=["EPSON TM-T20III Receipt", "Microsoft Print to PDF"],
            default_printer="Microsoft Print to PDF",
            queue_count=1,
            last_error="",
        )

        self.assertEqual(result["status"], "PASS")
        self.assertIn("SumatraPDF", result["summary"])
        self.assertIn("EPSON TM-T20III Receipt", result["summary"])
        self.assertIn("driver térmico validado", result["guidance"])
        self.assertIn("Trabajos en cola: 1", result["details"])

    def test_reports_actionable_failure_when_sumatra_or_printer_missing(self):
        result = build_printer_diagnostics(
            sumatra_path=r"C:\Missing\SumatraPDF.exe",
            sumatra_exists=False,
            configured_printer="POS58 Printer",
            installed_printers=["Microsoft Print to PDF"],
            default_printer="Microsoft Print to PDF",
            queue_count=None,
            last_error="Printer not found: 'POS58 Printer'",
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertIn("SUMATRA_PATH no existe", result["summary"])
        self.assertIn("PRINTER_NAME no coincide", result["summary"])
        self.assertIn("No se promete compatibilidad", result["guidance"])
        self.assertIn("Printer not found", result["details"])


if __name__ == "__main__":
    unittest.main()
