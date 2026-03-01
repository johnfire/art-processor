"""Tests for Mastodon platform integration."""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from urllib.error import HTTPError, URLError

from src.app.social.mastodon import MastodonPlatform
from src.app.social.base import PostResult


@pytest.fixture
def mastodon():
    """Create MastodonPlatform with test credentials."""
    platform = MastodonPlatform()
    platform.instance_url = "https://mastodon.example.com"
    platform.access_token = "test_token_123"
    return platform


@pytest.fixture
def unconfigured_mastodon():
    """Create MastodonPlatform with no credentials."""
    platform = MastodonPlatform()
    platform.instance_url = ""
    platform.access_token = ""
    return platform


class TestMastodonIsConfigured:
    def test_configured(self, mastodon):
        assert mastodon.is_configured() is True

    def test_not_configured_no_url(self, unconfigured_mastodon):
        assert unconfigured_mastodon.is_configured() is False

    def test_not_configured_no_token(self):
        platform = MastodonPlatform()
        platform.instance_url = "https://example.com"
        platform.access_token = ""
        assert platform.is_configured() is False


class TestMastodonProperties:
    def test_name(self):
        platform = MastodonPlatform()
        assert platform.name == "mastodon"
        assert platform.display_name == "Mastodon"

    def test_supports(self):
        platform = MastodonPlatform()
        assert platform.supports_images is True
        assert platform.supports_video is True
        assert platform.max_text_length == 500

    def test_not_stub(self):
        platform = MastodonPlatform()
        assert platform._is_stub is False


class TestMastodonPostImage:
    def test_not_configured_returns_error(self, unconfigured_mastodon, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")
        result = unconfigured_mastodon.post_image(img, "test post")
        assert result.success is False
        assert "not configured" in result.error

    @patch("src.app.social.mastodon.urlopen")
    def test_successful_post(self, mock_urlopen, mastodon, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"\xff\xd8\xff\xe0fake jpeg")

        # Mock media upload response
        media_response = MagicMock()
        media_response.status = 200
        media_response.read.return_value = json.dumps({"id": "media_123"}).encode()
        media_response.__enter__ = lambda s: s
        media_response.__exit__ = MagicMock(return_value=False)

        # Mock status creation response
        status_response = MagicMock()
        status_response.status = 200
        status_response.read.return_value = json.dumps({
            "url": "https://mastodon.example.com/@user/12345"
        }).encode()
        status_response.__enter__ = lambda s: s
        status_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [media_response, status_response]

        result = mastodon.post_image(img, "Test post #art", "Alt text here")

        assert result.success is True
        assert result.post_url == "https://mastodon.example.com/@user/12345"
        assert mock_urlopen.call_count == 2


class TestMastodonPostImage:
    def test_media_upload_returns_no_id(self, mastodon, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"\xff\xd8\xff\xe0fake jpeg")

        media_response = MagicMock()
        media_response.status = 200
        media_response.read.return_value = json.dumps({}).encode()  # no "id"
        media_response.__enter__ = lambda s: s
        media_response.__exit__ = MagicMock(return_value=False)

        with patch("src.app.social.mastodon.urlopen", return_value=media_response):
            result = mastodon.post_image(img, "Test post")

        assert result.success is False
        assert "Failed to upload media" in result.error

    @patch("src.app.social.mastodon.urlopen")
    def test_http_error_returns_failure(self, mock_urlopen, mastodon, tmp_path):
        import io
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg")
        mock_urlopen.side_effect = HTTPError(
            url="https://mastodon.example.com/api/v2/media",
            code=422,
            msg="Unprocessable Entity",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"Validation failed"}'),
        )
        result = mastodon.post_image(img, "Test post")
        assert result.success is False
        assert "422" in result.error

    @patch("src.app.social.mastodon.urlopen")
    def test_url_error_returns_failure(self, mock_urlopen, mastodon, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg")
        mock_urlopen.side_effect = URLError("Connection refused")
        result = mastodon.post_image(img, "Test post")
        assert result.success is False
        assert "Connection error" in result.error


class TestMastodonPostVideo:
    def test_not_configured_returns_error(self, unconfigured_mastodon, tmp_path):
        vid = tmp_path / "test.mp4"
        vid.write_bytes(b"fake video data")
        result = unconfigured_mastodon.post_video(vid, "test post")
        assert result.success is False
        assert "not configured" in result.error

    @patch("src.app.social.mastodon.urlopen")
    def test_successful_video_post(self, mock_urlopen, mastodon, tmp_path):
        vid = tmp_path / "test.mp4"
        vid.write_bytes(b"fake video data")

        media_response = MagicMock()
        media_response.status = 200
        media_response.read.return_value = json.dumps({"id": "vid_456"}).encode()
        media_response.__enter__ = lambda s: s
        media_response.__exit__ = MagicMock(return_value=False)

        status_response = MagicMock()
        status_response.status = 200
        status_response.read.return_value = json.dumps({
            "url": "https://mastodon.example.com/@user/99"
        }).encode()
        status_response.__enter__ = lambda s: s
        status_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [media_response, status_response]

        result = mastodon.post_video(vid, "New video #art")
        assert result.success is True
        assert result.post_url == "https://mastodon.example.com/@user/99"

    @patch("src.app.social.mastodon.urlopen")
    def test_video_upload_http_error(self, mock_urlopen, mastodon, tmp_path):
        import io
        vid = tmp_path / "test.mp4"
        vid.write_bytes(b"fake video data")
        mock_urlopen.side_effect = HTTPError(
            url="https://mastodon.example.com/api/v2/media",
            code=413,
            msg="Payload Too Large",
            hdrs=None,
            fp=io.BytesIO(b"too big"),
        )
        result = mastodon.post_video(vid, "Test video")
        assert result.success is False
        assert "413" in result.error

    @patch("src.app.social.mastodon.urlopen")
    def test_video_upload_no_id(self, mock_urlopen, mastodon, tmp_path):
        vid = tmp_path / "test.mp4"
        vid.write_bytes(b"fake video data")

        media_response = MagicMock()
        media_response.read.return_value = json.dumps({}).encode()
        media_response.__enter__ = lambda s: s
        media_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.return_value = media_response
        result = mastodon.post_video(vid, "Test video")
        assert result.success is False
        assert "Failed to upload video" in result.error


class TestMastodonVerifyCredentials:
    def test_not_configured(self, unconfigured_mastodon):
        assert unconfigured_mastodon.verify_credentials() is False

    @patch("src.app.social.mastodon.urlopen")
    def test_valid_credentials(self, mock_urlopen, mastodon):
        response = MagicMock()
        response.status = 200
        response.__enter__ = lambda s: s
        response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = response

        assert mastodon.verify_credentials() is True

    @patch("src.app.social.mastodon.urlopen")
    def test_http_error_returns_false(self, mock_urlopen, mastodon):
        import io
        mock_urlopen.side_effect = HTTPError(
            url="https://mastodon.example.com/api/v1/accounts/verify_credentials",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b"Unauthorized"),
        )
        assert mastodon.verify_credentials() is False

    @patch("src.app.social.mastodon.urlopen")
    def test_url_error_returns_false(self, mock_urlopen, mastodon):
        mock_urlopen.side_effect = URLError("Name resolution failed")
        assert mastodon.verify_credentials() is False
