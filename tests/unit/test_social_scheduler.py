"""Tests for social media scheduler."""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.app.social.scheduler import Scheduler, _get_image_path, _update_social_media_tracking


@pytest.fixture
def schedule_file(tmp_path):
    return tmp_path / "schedule.json"


@pytest.fixture
def scheduler(schedule_file):
    return Scheduler(schedule_file)


class TestScheduler:
    def test_empty_schedule(self, scheduler):
        assert scheduler.get_pending() == []
        assert scheduler.get_upcoming() == []
        assert scheduler.get_history() == []

    def test_add_post(self, scheduler):
        post_id = scheduler.add_post(
            content_id="test_painting",
            metadata_path="/path/to/meta.json",
            platform="mastodon",
            scheduled_time="2030-01-01T10:00:00",
        )
        assert post_id
        assert len(scheduler.data["scheduled_posts"]) == 1

    def test_add_post_persists(self, scheduler, schedule_file):
        scheduler.add_post(
            content_id="test",
            metadata_path="/path/meta.json",
            platform="mastodon",
            scheduled_time="2030-01-01T10:00:00",
        )
        # Reload from file
        new_scheduler = Scheduler(schedule_file)
        assert len(new_scheduler.data["scheduled_posts"]) == 1

    def test_get_pending_past_time(self, scheduler):
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        scheduler.add_post("test", "/path", "mastodon", past)
        assert len(scheduler.get_pending()) == 1

    def test_get_upcoming_future_time(self, scheduler):
        future = (datetime.now() + timedelta(days=1)).isoformat()
        scheduler.add_post("test", "/path", "mastodon", future)
        assert len(scheduler.get_upcoming()) == 1
        assert len(scheduler.get_pending()) == 0

    def test_cancel_post(self, scheduler):
        future = (datetime.now() + timedelta(days=1)).isoformat()
        post_id = scheduler.add_post("test", "/path", "mastodon", future)
        assert scheduler.cancel_post(post_id) is True
        assert len(scheduler.get_upcoming()) == 0

    def test_cancel_nonexistent_post(self, scheduler):
        assert scheduler.cancel_post("nonexistent") is False

    def test_mark_posted(self, scheduler):
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        post_id = scheduler.add_post("test", "/path", "mastodon", past)
        scheduler.mark_posted(post_id, "https://example.com/post/123")
        history = scheduler.get_history()
        assert len(history) == 1
        assert history[0]["status"] == "posted"
        assert history[0]["post_url"] == "https://example.com/post/123"

    def test_mark_failed(self, scheduler):
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        post_id = scheduler.add_post("test", "/path", "mastodon", past)
        scheduler.mark_failed(post_id, "Connection timeout")
        history = scheduler.get_history()
        assert len(history) == 1
        assert history[0]["status"] == "failed"
        assert history[0]["error"] == "Connection timeout"

    def test_history_limit(self, scheduler):
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        for i in range(10):
            post_id = scheduler.add_post(f"test_{i}", "/path", "mastodon", past)
            scheduler.mark_posted(post_id)
        assert len(scheduler.get_history(limit=5)) == 5


class TestGetImagePath:
    def test_instagram_string(self, tmp_path):
        img = tmp_path / "test.jpg"
        img.touch()
        metadata = {"files": {"instagram": str(img), "big": None}}
        assert _get_image_path(metadata) == img

    def test_instagram_list(self, tmp_path):
        img = tmp_path / "test.jpg"
        img.touch()
        metadata = {"files": {"instagram": [str(img)], "big": None}}
        assert _get_image_path(metadata) == img

    def test_fallback_to_big(self, tmp_path):
        # Big files are no longer used for social media (5MB API limit)
        img = tmp_path / "test.jpg"
        img.touch()
        metadata = {"files": {"instagram": None, "big": str(img)}}
        assert _get_image_path(metadata) is None

    def test_big_as_list(self, tmp_path):
        # Big files are no longer used for social media (5MB API limit)
        img = tmp_path / "test.jpg"
        img.touch()
        metadata = {"files": {"instagram": None, "big": [str(img)]}}
        assert _get_image_path(metadata) is None

    def test_no_files(self):
        metadata = {"files": {"instagram": None, "big": None}}
        assert _get_image_path(metadata) is None

    def test_missing_files_key(self):
        assert _get_image_path({}) is None


class TestUpdateSocialMediaTracking:
    def test_updates_existing_metadata(self, tmp_path):
        meta_file = tmp_path / "test.json"
        metadata = {
            "filename_base": "test",
            "social_media": {
                "mastodon": {"last_posted": None, "post_url": None, "post_count": 0}
            }
        }
        with open(meta_file, "w") as f:
            json.dump(metadata, f)

        _update_social_media_tracking(meta_file, metadata, "mastodon", "https://example.com/1")

        with open(meta_file, "r") as f:
            updated = json.load(f)

        assert updated["social_media"]["mastodon"]["post_count"] == 1
        assert updated["social_media"]["mastodon"]["post_url"] == "https://example.com/1"
        assert updated["social_media"]["mastodon"]["last_posted"] is not None

    def test_increments_count(self, tmp_path):
        meta_file = tmp_path / "test.json"
        metadata = {
            "filename_base": "test",
            "social_media": {
                "mastodon": {"last_posted": "2026-01-01", "post_url": "old", "post_count": 3}
            }
        }
        with open(meta_file, "w") as f:
            json.dump(metadata, f)

        _update_social_media_tracking(meta_file, metadata, "mastodon", "https://new")

        with open(meta_file, "r") as f:
            updated = json.load(f)

        assert updated["social_media"]["mastodon"]["post_count"] == 4

    def test_creates_social_media_if_missing(self, tmp_path):
        meta_file = tmp_path / "test.json"
        metadata = {"filename_base": "test"}
        with open(meta_file, "w") as f:
            json.dump(metadata, f)

        _update_social_media_tracking(meta_file, metadata, "mastodon", "https://url")

        with open(meta_file, "r") as f:
            updated = json.load(f)

        assert "social_media" in updated
        assert updated["social_media"]["mastodon"]["post_count"] == 1

    def test_adds_missing_platform_to_existing_social_media(self, tmp_path):
        """Adds a new platform entry when social_media exists but platform key is absent."""
        meta_file = tmp_path / "test.json"
        metadata = {
            "filename_base": "test",
            "social_media": {},  # exists but platform not in it
        }
        with open(meta_file, "w") as f:
            json.dump(metadata, f)

        _update_social_media_tracking(meta_file, metadata, "mastodon", "https://url")

        with open(meta_file, "r") as f:
            updated = json.load(f)

        assert updated["social_media"]["mastodon"]["post_count"] == 1


class TestSchedulerDefaultFile:
    def test_default_schedule_file_used_when_none_given(self, tmp_path):
        """Scheduler() with no arg reads SCHEDULE_PATH from config."""
        fake_path = tmp_path / "schedule.json"
        with patch("config.settings.SCHEDULE_PATH", fake_path):
            s = Scheduler()
        assert s.schedule_file == fake_path


class TestExecutePending:
    """Tests for Scheduler.execute_pending()."""

    def _make_metadata_file(self, tmp_path, image_path=None):
        meta = {
            "filename_base": "test_painting",
            "category": "test-paintings",
            "title": {"selected": "Test"},
            "description": "A test painting.",
            "files": {
                "instagram": str(image_path) if image_path else None,
                "big": None,
            },
            "social_media": {
                "mastodon": {"last_posted": None, "post_url": None, "post_count": 0}
            },
        }
        meta_file = tmp_path / "test_painting.json"
        with open(meta_file, "w") as f:
            json.dump(meta, f)
        return meta_file

    def test_execute_pending_missing_metadata(self, tmp_path):
        schedule_file = tmp_path / "schedule.json"
        s = Scheduler(schedule_file)
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        s.add_post("test", str(tmp_path / "nonexistent.json"), "mastodon", past)

        results = s.execute_pending()

        assert results["failed"] == 1
        assert results["posted"] == 0

    def test_execute_pending_unknown_platform(self, tmp_path):
        schedule_file = tmp_path / "schedule.json"
        s = Scheduler(schedule_file)
        meta_file = self._make_metadata_file(tmp_path)
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        s.add_post("test", str(meta_file), "not_a_real_platform", past)

        results = s.execute_pending()

        assert results["failed"] == 1

    def test_execute_pending_platform_not_configured(self, tmp_path):
        schedule_file = tmp_path / "schedule.json"
        s = Scheduler(schedule_file)
        meta_file = self._make_metadata_file(tmp_path)
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        s.add_post("test", str(meta_file), "mastodon", past)

        mock_platform = MagicMock()
        mock_platform.is_configured.return_value = False
        mock_platform.display_name = "Mastodon"

        with patch("src.app.social.get_platform", return_value=mock_platform):
            results = s.execute_pending()

        assert results["failed"] == 1

    def test_execute_pending_image_not_found(self, tmp_path):
        schedule_file = tmp_path / "schedule.json"
        s = Scheduler(schedule_file)
        # No actual image file — instagram path in metadata points to nonexistent file
        meta_file = self._make_metadata_file(tmp_path, image_path=tmp_path / "ghost.jpg")
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        s.add_post("test", str(meta_file), "mastodon", past)

        mock_platform = MagicMock()
        mock_platform.is_configured.return_value = True

        with patch("src.app.social.get_platform", return_value=mock_platform), \
             patch("src.app.social.formatter.format_post_text", return_value="text"):
            results = s.execute_pending()

        assert results["failed"] == 1

    def test_execute_pending_success(self, tmp_path):
        schedule_file = tmp_path / "schedule.json"
        s = Scheduler(schedule_file)
        image_path = tmp_path / "painting.jpg"
        image_path.touch()
        meta_file = self._make_metadata_file(tmp_path, image_path=image_path)
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        s.add_post("test", str(meta_file), "mastodon", past)

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.post_url = "https://mastodon.social/@test/123"

        mock_platform = MagicMock()
        mock_platform.is_configured.return_value = True
        mock_platform.post_image.return_value = mock_result

        with patch("src.app.social.get_platform", return_value=mock_platform), \
             patch("src.app.social.formatter.format_post_text", return_value="Post text"):
            results = s.execute_pending()

        assert results["posted"] == 1
        assert results["failed"] == 0


class TestGetImagePathConstructed:
    """Tests for constructed instagram path fallback in _get_image_path."""

    def test_constructed_path_from_big_filename(self, tmp_path):
        """Falls back to constructed PAINTINGS_INSTAGRAM_PATH / collection / filename."""
        collection = "landscapes"
        filename = "sunset.jpg"
        (tmp_path / collection).mkdir()
        (tmp_path / collection / filename).touch()

        metadata = {
            "filename_base": "sunset",
            "collection_folder": collection,
            "files": {
                "instagram": None,
                "big": str(tmp_path / "big" / collection / filename),
            },
        }

        with patch("config.settings.PAINTINGS_INSTAGRAM_PATH", tmp_path):
            result = _get_image_path(metadata)

        assert result is not None
        assert result.name == filename

    def test_constructed_path_filename_base_fallback(self, tmp_path):
        """Falls back to filename_base.jpg when no big file path available."""
        collection = "landscapes"
        (tmp_path / collection).mkdir()
        (tmp_path / collection / "sunset.jpg").touch()

        metadata = {
            "filename_base": "sunset",
            "collection_folder": collection,
            "files": {"instagram": None, "big": None},
        }

        with patch("config.settings.PAINTINGS_INSTAGRAM_PATH", tmp_path):
            result = _get_image_path(metadata)

        assert result is not None
        assert result.name == "sunset.jpg"
