import logging
import os
import unittest
from unittest.mock import patch


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(self.format(record))


class DesktopSlowLogTests(unittest.TestCase):
    def capture_messages(self, logger):
        handler = ListHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        return handler

    def test_fast_operation_stays_quiet(self):
        from utils.slowlog import log_if_slow

        logger = logging.getLogger("tests.desktop.slowlog.fast")
        handler = self.capture_messages(logger)
        try:
            with patch.dict(os.environ, {"SLOW_DESKTOP_MS": "1000"}, clear=False):
                emitted = log_if_slow(
                    logger,
                    threshold_env="SLOW_DESKTOP_MS",
                    default_ms=1000,
                    area="desktop",
                    operation="dashboard_refresh",
                    duration_ms=999.0,
                    context={"screen": "dashboard"},
                )
        finally:
            logger.removeHandler(handler)

        self.assertFalse(emitted)
        self.assertEqual(handler.messages, [])

    def test_slow_operation_logs_safe_context_and_redacts_secrets(self):
        from utils.slowlog import log_if_slow

        logger = logging.getLogger("tests.desktop.slowlog.slow")
        handler = self.capture_messages(logger)
        try:
            with patch.dict(os.environ, {"SLOW_DESKTOP_MS": "1000"}, clear=False):
                emitted = log_if_slow(
                    logger,
                    threshold_env="SLOW_DESKTOP_MS",
                    default_ms=1000,
                    area="desktop",
                    operation="registration",
                    duration_ms=1001.5,
                    context={"patente": "ABC123", "password": "secret-value"},
                )
        finally:
            logger.removeHandler(handler)

        self.assertTrue(emitted)
        message = handler.messages[0]
        self.assertIn("slow_operation", message)
        self.assertIn("area=desktop", message)
        self.assertIn("operation=registration", message)
        self.assertIn("duration_ms=1001.50", message)
        self.assertIn("patente=ABC123", message)
        self.assertIn("password=[REDACTED]", message)
        self.assertNotIn("secret-value", message)

    def test_disabled_threshold_does_not_log(self):
        from utils.slowlog import log_if_slow

        logger = logging.getLogger("tests.desktop.slowlog.disabled")
        handler = self.capture_messages(logger)
        try:
            with patch.dict(os.environ, {"SLOW_DESKTOP_MS": "0"}, clear=False):
                emitted = log_if_slow(
                    logger,
                    threshold_env="SLOW_DESKTOP_MS",
                    default_ms=1000,
                    area="desktop",
                    operation="print",
                    duration_ms=5000.0,
                    context={"printer": "POS58"},
                )
        finally:
            logger.removeHandler(handler)

        self.assertFalse(emitted)
        self.assertEqual(handler.messages, [])


if __name__ == "__main__":
    unittest.main()
