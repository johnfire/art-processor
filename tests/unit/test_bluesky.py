"""Tests for Bluesky platform integration."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.app.social.bluesky import BlueskyPlatform
from src.app.social.base import PostResult


@pytest.fixture
def bluesky():
    """Create BlueskyPlatform with test credentials."""
    platform = BlueskyPlatform()
    platform.handle = "test.bsky.social"
    platform.app_password = "test-app-password"
    return platform


@pytest.fixture
def unconfigured_bluesky():
    """Create BlueskyPlatform with no credentials."""
    platform = BlueskyPlatform()
    platform.handle = ""
    platform.app_password = ""
    return platform


class TestBlueskyProperties:
    def test_name(self):
        platform = BlueskyPlatform()
        assert platform.name == "bluesky"
        assert platform.display_name == "Bluesky"

    def test_supports(self):
        platform = BlueskyPlatform()
        assert platform.supports_images is True
        assert platform.supports_video is False
        assert platform.max_text_length == 300

    def test_not_stub(self):
        platform = BlueskyPlatform()
        assert platform._is_stub is False


class TestBlueskyIsConfigured:
    def test_configured(self, bluesky):
        assert bluesky.is_configured() is True

    def test_not_configured_no_handle(self):
        platform = BlueskyPlatform()
        platform.handle = ""
        platform.app_password = "some-password"
        assert platform.is_configured() is False

    def test_not_configured_no_password(self):
        platform = BlueskyPlatform()
        platform.handle = "test.bsky.social"
        platform.app_password = ""
        assert platform.is_configured() is False


class TestBlueskyVerifyCredentials:
    def test_not_configured(self, unconfigured_bluesky):
        assert unconfigured_bluesky.verify_credentials() is False

    def test_valid_credentials(self, bluesky):
        mock_client = MagicMock()
        with patch.object(bluesky, "_get_client", return_value=mock_client):
            assert bluesky.verify_credentials() is True

    def test_invalid_credentials_raises(self, bluesky):
        with patch.object(bluesky, "_get_client", side_effect=Exception("Invalid password")):
            with pytest.raises(RuntimeError, match="Bluesky login failed"):
                bluesky.verify_credentials()


class TestBlueskyPostImage:
    def test_not_configured_returns_error(self, unconfigured_bluesky, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")
        result = unconfigured_bluesky.post_image(img, "test post")
        assert result.success is False
        assert "not configured" in result.error

    def test_text_too_long_returns_error(self, bluesky, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")
        result = bluesky.post_image(img, "x" * 301)
        assert result.success is False
        assert "300" in result.error

    @patch("atproto.models")
    def test_successful_post(self, mock_models, bluesky, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg data")

        mock_client = MagicMock()
        mock_client.upload_blob.return_value.blob = MagicMock()
        mock_client.send_post.return_value.uri = "at://did:plc:abc123/app.bsky.feed.post/123"

        with patch.object(bluesky, "_get_client", return_value=mock_client), \
             patch.object(bluesky, "_strip_exif", return_value=b"clean_image_data"):
            result = bluesky.post_image(img, "Test post #art", "A landscape painting")

        assert result.success is True
        assert result.post_url == "at://did:plc:abc123/app.bsky.feed.post/123"
        mock_client.upload_blob.assert_called_once_with(b"clean_image_data")
        mock_client.send_post.assert_called_once()

    @patch("atproto.models")
    def test_client_error_returns_failure(self, mock_models, bluesky, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg data")

        with patch.object(bluesky, "_get_client", side_effect=Exception("Network error")), \
             patch.object(bluesky, "_strip_exif", return_value=b"data"):
            result = bluesky.post_image(img, "Test post")

        assert result.success is False
        assert "Network error" in result.error


class TestBlueskyPostVideo:
    def test_raises_not_implemented(self, bluesky, tmp_path):
        vid = tmp_path / "test.mp4"
        vid.write_bytes(b"fake video data")
        with pytest.raises(NotImplementedError):
            bluesky.post_video(vid, "test post")


class TestBlueskyStripExif:
    def test_returns_bytes(self, bluesky, tmp_path):
        from PIL import Image as PILImage
        import io

        # Create a minimal real JPEG in a temp file
        img = PILImage.new("RGB", (10, 10), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(buf.getvalue())

        result = bluesky._strip_exif(img_path)
        assert isinstance(result, bytes)
        assert len(result) > 0
