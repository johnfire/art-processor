"""Tests for Pixelfed platform integration."""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.app.social.pixelfed import PixelfedPlatform
from src.app.social.base import PostResult


@pytest.fixture
def pixelfed():
    """Create PixelfedPlatform with test credentials."""
    platform = PixelfedPlatform()
    platform.instance_url = "https://pixelfed.example.com"
    platform.access_token = "test_token_123"
    return platform


@pytest.fixture
def unconfigured_pixelfed():
    """Create PixelfedPlatform with no credentials."""
    platform = PixelfedPlatform()
    platform.instance_url = ""
    platform.access_token = ""
    return platform


class TestPixelfedProperties:
    def test_name(self):
        platform = PixelfedPlatform()
        assert platform.name == "pixelfed"
        assert platform.display_name == "Pixelfed"

    def test_supports(self):
        platform = PixelfedPlatform()
        assert platform.supports_images is True
        assert platform.supports_video is False
        assert platform.max_text_length == 2000

    def test_not_stub(self):
        platform = PixelfedPlatform()
        assert platform._is_stub is False


class TestPixelfedIsConfigured:
    def test_configured(self, pixelfed):
        assert pixelfed.is_configured() is True

    def test_not_configured_no_url(self, unconfigured_pixelfed):
        assert unconfigured_pixelfed.is_configured() is False

    def test_not_configured_no_token(self):
        platform = PixelfedPlatform()
        platform.instance_url = "https://pixelfed.example.com"
        platform.access_token = ""
        assert platform.is_configured() is False


class TestPixelfedVerifyCredentials:
    def test_not_configured(self, unconfigured_pixelfed):
        assert unconfigured_pixelfed.verify_credentials() is False

    @patch("src.app.social.pixelfed.urlopen")
    def test_valid_credentials(self, mock_urlopen, pixelfed):
        response = MagicMock()
        response.status = 200
        response.__enter__ = lambda s: s
        response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = response

        assert pixelfed.verify_credentials() is True

    @patch("src.app.social.pixelfed.urlopen")
    def test_invalid_credentials(self, mock_urlopen, pixelfed):
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(
            url="https://pixelfed.example.com/api/v1/accounts/verify_credentials",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
        assert pixelfed.verify_credentials() is False


class TestPixelfedPostImage:
    def test_not_configured_returns_error(self, unconfigured_pixelfed, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")
        result = unconfigured_pixelfed.post_image(img, "test post")
        assert result.success is False
        assert "not configured" in result.error

    @patch("src.app.social.pixelfed.urlopen")
    def test_successful_post(self, mock_urlopen, pixelfed, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"\xff\xd8\xff\xe0fake jpeg")

        # Mock media upload response (v1/media)
        media_response = MagicMock()
        media_response.status = 200
        media_response.read.return_value = json.dumps({"id": "media_456"}).encode()
        media_response.__enter__ = lambda s: s
        media_response.__exit__ = MagicMock(return_value=False)

        # Mock status creation response
        status_response = MagicMock()
        status_response.status = 200
        status_response.read.return_value = json.dumps({
            "url": "https://pixelfed.example.com/p/user/12345"
        }).encode()
        status_response.__enter__ = lambda s: s
        status_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [media_response, status_response]

        result = pixelfed.post_image(img, "Test post #art", "A landscape painting")

        assert result.success is True
        assert result.post_url == "https://pixelfed.example.com/p/user/12345"
        assert mock_urlopen.call_count == 2

    @patch("src.app.social.pixelfed.urlopen")
    def test_media_upload_returns_no_id(self, mock_urlopen, pixelfed, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg")

        media_response = MagicMock()
        media_response.status = 200
        media_response.read.return_value = json.dumps({}).encode()  # no "id" field
        media_response.__enter__ = lambda s: s
        media_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.return_value = media_response

        result = pixelfed.post_image(img, "Test post")
        assert result.success is False
        assert "Failed to upload media" in result.error

    @patch("src.app.social.pixelfed.urlopen")
    def test_http_error_returns_failure(self, mock_urlopen, pixelfed, tmp_path):
        from urllib.error import HTTPError
        import io
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg")

        mock_urlopen.side_effect = HTTPError(
            url="https://pixelfed.example.com/api/v1/media",
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"Unauthenticated."}'),
        )

        result = pixelfed.post_image(img, "Test post")
        assert result.success is False
        assert "500" in result.error


class TestPixelfedPostVideo:
    def test_raises_not_implemented(self, pixelfed, tmp_path):
        vid = tmp_path / "test.mp4"
        vid.write_bytes(b"fake video data")
        with pytest.raises(NotImplementedError):
            pixelfed.post_video(vid, "test post")
