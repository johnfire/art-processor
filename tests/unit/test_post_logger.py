"""Tests for the social media post logger."""

import logging
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_logger():
    """Clear handlers between tests so each gets a fresh FileHandler."""
    yield
    logger = logging.getLogger("theo.social.posts")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


@pytest.fixture
def log_dir(tmp_path):
    d = tmp_path / "logs"
    d.mkdir()
    return d


@pytest.fixture
def screenshot_dir(tmp_path):
    d = tmp_path / "screenshots"
    d.mkdir()
    return d


def _read_log(log_dir):
    return (log_dir / "social.log").read_text()


class TestLogPostSuccess:
    def test_creates_log_file(self, log_dir, tmp_path):
        from src.app.social.post_logger import log_post_success
        with patch("config.settings.LOGS_DIR", log_dir):
            log_post_success("mastodon", "My Painting", tmp_path / "test.jpg", "https://example.com/1")
        assert (log_dir / "social.log").exists()

    def test_contains_platform_and_title(self, log_dir, tmp_path):
        from src.app.social.post_logger import log_post_success
        with patch("config.settings.LOGS_DIR", log_dir):
            log_post_success("bluesky", "Sunset Over Delft", tmp_path / "img.jpg", None)
        content = _read_log(log_dir)
        assert "SUCCESS" in content
        assert "bluesky" in content
        assert "Sunset Over Delft" in content

    def test_contains_url_when_provided(self, log_dir, tmp_path):
        from src.app.social.post_logger import log_post_success
        with patch("config.settings.LOGS_DIR", log_dir):
            log_post_success("tumblr", "Canal Scene", tmp_path / "img.jpg", "https://tumblr.com/post/99")
        assert "https://tumblr.com/post/99" in _read_log(log_dir)

    def test_no_url_when_none(self, log_dir, tmp_path):
        from src.app.social.post_logger import log_post_success
        with patch("config.settings.LOGS_DIR", log_dir):
            log_post_success("mastodon", "Storm Painting", tmp_path / "img.jpg", None)
        content = _read_log(log_dir)
        assert "url=" not in content

    def test_no_image_part_when_none(self, log_dir):
        from src.app.social.post_logger import log_post_success
        with patch("config.settings.LOGS_DIR", log_dir):
            log_post_success("mastodon", "Storm Painting", None, None)
        content = _read_log(log_dir)
        assert "image=" not in content

    def test_contains_image_path(self, log_dir, tmp_path):
        from src.app.social.post_logger import log_post_success
        img = tmp_path / "canal.jpg"
        with patch("config.settings.LOGS_DIR", log_dir):
            log_post_success("mastodon", "Canal", img, None)
        assert "canal.jpg" in _read_log(log_dir)


class TestLogPostFailure:
    def test_creates_log_file(self, log_dir, screenshot_dir, tmp_path):
        from src.app.social.post_logger import log_post_failure
        with patch("config.settings.LOGS_DIR", log_dir), \
             patch("config.settings.SCREENSHOTS_DIR", screenshot_dir):
            log_post_failure("bluesky", "The Beach", tmp_path / "img.jpg", "Text too long")
        assert (log_dir / "social.log").exists()

    def test_contains_failure_fields(self, log_dir, screenshot_dir, tmp_path):
        from src.app.social.post_logger import log_post_failure
        with patch("config.settings.LOGS_DIR", log_dir), \
             patch("config.settings.SCREENSHOTS_DIR", screenshot_dir):
            log_post_failure("pixelfed", "Mountain View", tmp_path / "img.jpg", "HTTP 500")
        content = _read_log(log_dir)
        assert "FAILURE" in content
        assert "pixelfed" in content
        assert "Mountain View" in content
        assert "HTTP 500" in content

    def test_no_screenshots_for_non_playwright_platform(self, log_dir, screenshot_dir, tmp_path):
        from src.app.social.post_logger import log_post_failure
        # Put a png in the screenshot dir to make sure it's NOT included
        (screenshot_dir / "bluesky_error.png").write_bytes(b"fake")
        with patch("config.settings.LOGS_DIR", log_dir), \
             patch("config.settings.SCREENSHOTS_DIR", screenshot_dir):
            log_post_failure("bluesky", "My Art", tmp_path / "img.jpg", "Network error")
        assert "screenshots:" not in _read_log(log_dir)

    def test_includes_screenshots_for_cara(self, log_dir, screenshot_dir, tmp_path):
        from src.app.social.post_logger import log_post_failure
        # Create fake cara screenshots
        (screenshot_dir / "cara_01_home.png").write_bytes(b"fake")
        (screenshot_dir / "cara_error.png").write_bytes(b"fake")
        with patch("config.settings.LOGS_DIR", log_dir), \
             patch("config.settings.SCREENSHOTS_DIR", screenshot_dir):
            log_post_failure("cara", "The Dunes", tmp_path / "img.jpg", "Timeout")
        content = _read_log(log_dir)
        assert "screenshots:" in content
        assert "cara_error.png" in content

    def test_no_screenshots_section_when_none_exist(self, log_dir, screenshot_dir, tmp_path):
        from src.app.social.post_logger import log_post_failure
        # Screenshot dir is empty
        with patch("config.settings.LOGS_DIR", log_dir), \
             patch("config.settings.SCREENSHOTS_DIR", screenshot_dir):
            log_post_failure("cara", "The Dunes", tmp_path / "img.jpg", "Timeout")
        assert "screenshots:" not in _read_log(log_dir)

    def test_no_image_part_when_none(self, log_dir, screenshot_dir):
        from src.app.social.post_logger import log_post_failure
        with patch("config.settings.LOGS_DIR", log_dir), \
             patch("config.settings.SCREENSHOTS_DIR", screenshot_dir):
            log_post_failure("mastodon", "Painting", None, "Some error")
        assert "image:" not in _read_log(log_dir)


class TestLogCredentialFailure:
    def test_creates_log_entry(self, log_dir):
        from src.app.social.post_logger import log_credential_failure
        with patch("config.settings.LOGS_DIR", log_dir):
            log_credential_failure("pixelfed")
        content = _read_log(log_dir)
        assert "CREDENTIAL FAILURE" in content
        assert "pixelfed" in content

    def test_different_platforms(self, log_dir):
        from src.app.social.post_logger import log_credential_failure
        with patch("config.settings.LOGS_DIR", log_dir):
            log_credential_failure("tumblr")
        assert "tumblr" in _read_log(log_dir)


class TestGetLoggerIdempotent:
    def test_multiple_calls_dont_add_extra_handlers(self, log_dir):
        from src.app.social.post_logger import _get_logger
        with patch("config.settings.LOGS_DIR", log_dir):
            _get_logger()
            _get_logger()
            _get_logger()
        logger = logging.getLogger("theo.social.posts")
        assert len(logger.handlers) == 1
