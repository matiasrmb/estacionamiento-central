import unittest

from utils.plates import normalizar_patente, validar_patente


class PlateTests(unittest.TestCase):
    def test_accepts_all_supported_formats(self):
        for patente in ("ABCD12", "ABC12", "AB123CD", "ABC123"):
            with self.subTest(patente=patente):
                self.assertTrue(validar_patente(patente))

    def test_normalizes_lowercase_spaces_and_hyphens_only(self):
        self.assertEqual(normalizar_patente("ab-cd 12"), "ABCD12")
        self.assertEqual(normalizar_patente("ab-123 cd"), "AB123CD")

    def test_rejects_special_and_accented_characters(self):
        for patente in ("AB{CD12", "AB[CD12", "ABCD1'2", "ÁBCD12", "ABCD.12"):
            with self.subTest(patente=patente):
                self.assertFalse(validar_patente(patente))
