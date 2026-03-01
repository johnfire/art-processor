"""Tests for Tumblr platform integration."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.app.social.tumblr import TumblrPlatform
from src.app.social.base import PostResult


@pytest.fixture
def tumblr():
    """Create TumblrPlatform with test credentials."""
    platform = TumblrPlatform()
    platform.consumer_key = "test_consumer_key"
    platform.consumer_secret = "test_consumer_secret"
    platform.oauth_token = "test_oauth_token"
    platform.oauth_secret = "test_oauth_secret"
    platform.blog_name = "test-art-blog"
    return platform


@pytest.fixture
def unconfigured_tumblr():
    """Create TumblrPlatform with no credentials."""
    platform = TumblrPlatform()
    platform.consumer_key = ""
    platform.consumer_secret = ""
    platform.oauth_token = ""
    platform.oauth_secret = ""
    platform.blog_name = ""
    return platform


def _mock_client(post_id="99999"):
    """Return a mock pytumblr client with sensible defaults.

    pytumblr returns the response body directly (no meta wrapper):
      info()         → {"user": {...}}
      create_photo() → {"id": 12345, ...}
    """
    client = MagicMock()
    client.info.return_value = {"user": {"name": "test-user"}}
    client.create_photo.return_value = {"id": post_id}
    return client


class TestTumblrProperties:
    def test_name(self):
        platform = TumblrPlatform()
        assert platform.name == "tumblr"
        assert platform.display_name == "Tumblr"

    def test_supports(self):
        platform = TumblrPlatform()
        assert platform.supports_images is True
        assert platform.supports_video is False

    def test_not_stub(self):
        platform = TumblrPlatform()
        assert platform._is_stub is False


class TestTumblrIsConfigured:
    def test_configured(self, tumblr):
        assert tumblr.is_configured() is True

    def test_not_configured_missing_consumer_key(self):
        platform = TumblrPlatform()
        platform.consumer_key = ""
        platform.consumer_secret = "s"
        platform.oauth_token = "t"
        platform.oauth_secret = "os"
        platform.blog_name = "blog"
        assert platform.is_configured() is False

    def test_not_configured_missing_blog_name(self):
        platform = TumblrPlatform()
        platform.consumer_key = "ck"
        platform.consumer_secret = "cs"
        platform.oauth_token = "ot"
        platform.oauth_secret = "os"
        platform.blog_name = ""
        assert platform.is_configured() is False

    def test_not_configured_all_empty(self, unconfigured_tumblr):
        assert unconfigured_tumblr.is_configured() is False


class TestTumblrVerifyCredentials:
    def test_not_configured(self, unconfigured_tumblr):
        assert unconfigured_tumblr.verify_credentials() is False

    def test_valid_credentials(self, tumblr):
        with patch.object(tumblr, "_get_client", return_value=_mock_client()):
            assert tumblr.verify_credentials() is True

    def test_api_error_returns_false(self, tumblr):
        client = MagicMock()
        client.info.return_value = {"errors": [{"title": "Unauthorized"}]}
        with patch.object(tumblr, "_get_client", return_value=client):
            assert tumblr.verify_credentials() is False

    def test_exception_returns_false(self, tumblr):
        with patch.object(tumblr, "_get_client", side_effect=Exception("Network error")):
            assert tumblr.verify_credentials() is False


class TestTumblrPostImage:
    def test_not_configured_returns_error(self, unconfigured_tumblr, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")
        result = unconfigured_tumblr.post_image(img, "test post")
        assert result.success is False
        assert "not configured" in result.error

    def test_successful_post(self, tumblr, tmp_path):
        img = tmp_path / "painting.jpg"
        img.write_bytes(b"fake jpeg data")

        with patch.object(tumblr, "_get_client", return_value=_mock_client(post_id="42")):
            result = tumblr.post_image(img, "A painting #art")

        assert result.success is True
        assert result.post_url == "https://test-art-blog.tumblr.com/post/42"

    def test_api_error_response_returns_failure(self, tumblr, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg data")

        client = MagicMock()
        client.create_photo.return_value = {"errors": [{"title": "Unauthorized", "code": 1016}]}
        with patch.object(tumblr, "_get_client", return_value=client):
            result = tumblr.post_image(img, "Test post")

        assert result.success is False
        assert "Unauthorized" in result.error

    def test_exception_returns_failure(self, tumblr, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg data")

        with patch.object(tumblr, "_get_client", side_effect=Exception("Connection refused")):
            result = tumblr.post_image(img, "Test post")

        assert result.success is False
        assert "Connection refused" in result.error


class TestTumblrPostImageWithTags:
    def test_successful_post_with_tags(self, tumblr, tmp_path):
        img = tmp_path / "painting.jpg"
        img.write_bytes(b"fake jpeg data")
        tags = ["art", "painting", "oilpainting"]

        client = _mock_client(post_id="55")
        with patch.object(tumblr, "_get_client", return_value=client):
            result = tumblr.post_image_with_tags(img, "A painting", tags)

        assert result.success is True
        assert result.post_url == "https://test-art-blog.tumblr.com/post/55"
        # Tags should be passed to create_photo
        call_kwargs = client.create_photo.call_args[1]
        assert call_kwargs["tags"] == tags

    def test_tags_truncated_to_max(self, tumblr, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg data")
        tags = [f"tag{i}" for i in range(50)]  # 50 tags, limit is 30

        client = _mock_client()
        with patch.object(tumblr, "_get_client", return_value=client):
            tumblr.post_image_with_tags(img, "Test", tags)

        call_kwargs = client.create_photo.call_args[1]
        assert len(call_kwargs["tags"]) == 30

    def test_not_configured_returns_error(self, unconfigured_tumblr, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake jpeg data")
        result = unconfigured_tumblr.post_image_with_tags(img, "test", ["art"])
        assert result.success is False
        assert "not configured" in result.error


class TestTumblrPostVideo:
    def test_raises_not_implemented(self, tumblr, tmp_path):
        vid = tmp_path / "test.mp4"
        vid.write_bytes(b"fake video data")
        with pytest.raises(NotImplementedError):
            tumblr.post_video(vid, "test post")
