"""Tests for the centralized app logger."""
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path


def _clear_theo_logger():
    """Remove all handlers from the 'theo' logger so tests are isolated."""
    root = logging.getLogger("theo")
    root.handlers.clear()


class TestConfigureLogging:
    def setup_method(self):
        _clear_theo_logger()

    def teardown_method(self):
        _clear_theo_logger()

    def test_adds_handler_to_theo_logger(self, tmp_path):
        from src.core.logger import configure_logging

        with patch("src.core.logger.LOGS_DIR", tmp_path):
            configure_logging()

        root = logging.getLogger("theo")
        assert len(root.handlers) == 1

    def test_idempotent(self, tmp_path):
        """Calling configure_logging() twice should not add duplicate handlers."""
        from src.core.logger import configure_logging

        with patch("src.core.logger.LOGS_DIR", tmp_path):
            configure_logging()
            configure_logging()

        root = logging.getLogger("theo")
        assert len(root.handlers) == 1

    def test_log_level_is_debug(self, tmp_path):
        from src.core.logger import configure_logging

        with patch("src.core.logger.LOGS_DIR", tmp_path):
            configure_logging()

        root = logging.getLogger("theo")
        assert root.level == logging.DEBUG

    def test_creates_log_file(self, tmp_path):
        from src.core.logger import configure_logging

        with patch("src.core.logger.LOGS_DIR", tmp_path):
            configure_logging()
            log = logging.getLogger("theo.test")
            log.info("hello")

        assert (tmp_path / "app.log").exists()

    def test_does_not_propagate(self, tmp_path):
        from src.core.logger import configure_logging

        with patch("src.core.logger.LOGS_DIR", tmp_path):
            configure_logging()

        root = logging.getLogger("theo")
        assert root.propagate is False


class TestGetLogger:
    def test_returns_child_of_theo(self):
        from src.core.logger import get_logger

        log = get_logger("faso")
        assert log.name == "theo.faso"

    def test_returns_correct_name_for_nested(self):
        from src.core.logger import get_logger

        log = get_logger("social.daily")
        assert log.name == "theo.social.daily"

    def test_returns_logger_instance(self):
        from src.core.logger import get_logger

        log = get_logger("cli")
        assert isinstance(log, logging.Logger)
