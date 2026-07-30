import unittest
from pathlib import Path


class MensualesViewContractTests(unittest.TestCase):
    def test_monthly_form_exposes_contact_and_due_day_without_unsupported_getint_keywords(self):
        source = (Path(__file__).parents[1] / "views" / "mensuales.py").read_text(encoding="utf-8")

        self.assertIn("self.telefono_input", source)
        self.assertIn("self.vencimiento_input.setRange(1, 31)", source)
        self.assertIn('"Pago"', source)
        self.assertIn("QDialogButtonBox", source)
        self.assertNotIn("QInputDialog.getInt", source)


if __name__ == "__main__":
    unittest.main()
