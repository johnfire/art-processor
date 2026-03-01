"""Tests for Cara platform integration."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from src.app.social.cara import CaraPlatform
from src.app.social.base import PostResult


@pytest.fixture
def cara(tmp_path):
    """Create CaraPlatform with a valid session marker in a temp profile dir."""
    platform = CaraPlatform()
    platform.profile_dir = tmp_path / "cara_browser_profile"
    platform.profile_dir.mkdir()
    platform._marker = platform.profile_dir / ".logged_in"
    platform._marker.write_text("ok")
    return platform


@pytest.fixture
def unconfigured_cara(tmp_path):
    """Create CaraPlatform with no session marker (not logged in)."""
    platform = CaraPlatform()
    platform.profile_dir = tmp_path / "cara_browser_profile"
    platform.profile_dir.mkdir()
    platform._marker = platform.profile_dir / ".logged_in"
    # deliberately not writing the marker file
    return platform


class TestCaraProperties:
    def test_name(self):
        platform = CaraPlatform()
        assert platform.name == "cara"
        assert platform.display_name == "Cara"

    def test_supports(self):
        platform = CaraPlatform()
        assert platform.supports_images is True
        assert platform.supports_video is False
        assert platform.max_text_length == 2000

    def test_not_stub(self):
        platform = CaraPlatform()
        assert platform._is_stub is False


class TestCaraIsConfigured:
    def test_configured_when_marker_exists(self, cara):
        assert cara.is_configured() is True

    def test_not_configured_when_no_marker(self, unconfigured_cara):
        assert unconfigured_cara.is_configured() is False


class TestCaraVerifyCredentials:
    def test_returns_true_when_configured(self, cara):
        assert cara.verify_credentials() is True

    def test_returns_false_when_not_configured(self, unconfigured_cara):
        assert unconfigured_cara.verify_credentials() is False


class TestCaraPostImage:
    def test_not_configured_returns_error(self, unconfigured_cara, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")
        result = unconfigured_cara.post_image(img, "test post")
        assert result.success is False
        assert "cara-login" in result.error

    def test_successful_post(self, cara, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")

        expected = PostResult(success=True, post_url="https://cara.app/user/post/123")

        async def fake_post_async(image_path, text):
            return expected

        with patch.object(cara, "_post_image_async", side_effect=fake_post_async):
            result = cara.post_image(img, "Test post #art")

        assert result.success is True
        assert result.post_url == "https://cara.app/user/post/123"

    def test_async_exception_returns_failure(self, cara, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")

        async def fail_async(image_path, text):
            raise Exception("Playwright error")

        with patch.object(cara, "_post_image_async", side_effect=fail_async):
            result = cara.post_image(img, "Test post")

        assert result.success is False
        assert "Playwright error" in result.error


class TestCaraPostVideo:
    def test_raises_not_implemented(self, cara, tmp_path):
        vid = tmp_path / "test.mp4"
        vid.write_bytes(b"fake video data")
        with pytest.raises(NotImplementedError):
            cara.post_video(vid, "test post")


class TestCaraSessionExpiry:
    def test_marker_deleted_on_expired_session(self, cara, tmp_path):
        """If _post_image_async clears the marker, is_configured returns False afterwards."""
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")

        async def expired_session(image_path, text):
            # Simulate session expiry: code clears the marker
            cara._marker.unlink(missing_ok=True)
            return PostResult(success=False, error="Cara session expired. Run: python main.py cara-login")

        with patch.object(cara, "_post_image_async", side_effect=expired_session):
            result = cara.post_image(img, "Test post")

        assert result.success is False
        assert "session expired" in result.error
        assert cara.is_configured() is False
