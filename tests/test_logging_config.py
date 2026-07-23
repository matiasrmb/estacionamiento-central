import logging
import tempfile
import unittest
from pathlib import Path

from utils import logging_config


class LoggingConfigTests(unittest.TestCase):
    def setUp(self):
        self.root_logger = logging.getLogger()
        self.previous_level = self.root_logger.level
        self.managed_handlers = [
            handler
            for handler in self.root_logger.handlers
            if getattr(handler, logging_config._HANDLER_MARKER, False)
        ]
        for handler in self.managed_handlers:
            self.root_logger.removeHandler(handler)
        logging_config._LOG_PATH = None

    def tearDown(self):
        for handler in list(self.root_logger.handlers):
            if getattr(handler, logging_config._HANDLER_MARKER, False):
                self.root_logger.removeHandler(handler)
                handler.close()
        for handler in self.managed_handlers:
            self.root_logger.addHandler(handler)
        self.root_logger.setLevel(self.previous_level)
        logging_config._LOG_PATH = None

    def remove_current_managed_handlers(self):
        for handler in list(self.root_logger.handlers):
            if getattr(handler, logging_config._HANDLER_MARKER, False):
                self.root_logger.removeHandler(handler)
                handler.close()
        logging_config._LOG_PATH = None

    def test_setup_logging_creates_file_handler_under_logs_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                log_path = logging_config.setup_logging(base_path=temp_dir)

                self.assertEqual(log_path, Path(temp_dir) / "logs" / "desktop.log")
                self.assertTrue(log_path.parent.exists())
                file_handlers = [
                    handler
                    for handler in self.root_logger.handlers
                    if getattr(handler, logging_config._HANDLER_MARKER, False)
                    and hasattr(handler, "baseFilename")
                ]
                self.assertEqual(len(file_handlers), 1)
                self.assertEqual(Path(file_handlers[0].baseFilename), log_path)
            finally:
                self.remove_current_managed_handlers()

    def test_setup_logging_does_not_duplicate_handlers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                logging_config.setup_logging(base_path=temp_dir)
                first_handlers = [
                    handler
                    for handler in self.root_logger.handlers
                    if getattr(handler, logging_config._HANDLER_MARKER, False)
                ]

                logging_config.setup_logging(base_path=temp_dir)
                second_handlers = [
                    handler
                    for handler in self.root_logger.handlers
                    if getattr(handler, logging_config._HANDLER_MARKER, False)
                ]

                self.assertEqual(second_handlers, first_handlers)
            finally:
                self.remove_current_managed_handlers()


if __name__ == "__main__":
    unittest.main()
