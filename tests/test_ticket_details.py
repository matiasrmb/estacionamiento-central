import unittest
from datetime import datetime

from utils.ticket import build_ticket_detail_lines


class TicketDetailsTests(unittest.TestCase):
    def test_builds_wash_then_stay_detail_lines_with_total(self):
        lines = build_ticket_detail_lines({
            "lavado": {
                "inicio": datetime(2026, 7, 1, 10, 0),
                "fin": datetime(2026, 7, 1, 10, 30),
                "duracion_minutos": 30,
                "monto": 9000,
            },
            "estadia": {
                "inicio": datetime(2026, 7, 1, 10, 30),
                "fin": datetime(2026, 7, 1, 12, 0),
                "duracion_minutos": 90,
                "monto": 1500,
            },
        })

        self.assertEqual(lines, [
            "Lavado:",
            "Inicio: 01-07-2026 10:00:00",
            "Fin: 01-07-2026 10:30:00",
            "Duracion: 30 min",
            "Monto: $9000",
            "Estadia:",
            "Inicio: 01-07-2026 10:30:00",
            "Fin: 01-07-2026 12:00:00",
            "Duracion: 90 min",
            "Monto: $1500",
            "Total detalle: $10500",
        ])

    def test_returns_empty_lines_when_no_detail_sections_are_provided(self):
        self.assertEqual(build_ticket_detail_lines(None), [])
        self.assertEqual(build_ticket_detail_lines({}), [])


if __name__ == "__main__":
    unittest.main()
