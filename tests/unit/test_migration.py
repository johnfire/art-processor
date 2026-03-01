"""Tests for upload_status.json migration."""

import json
import pytest
from pathlib import Path

from src.app.services.migrate_tracking import migrate


@pytest.fixture
def migration_env(tmp_path):
    """Set up a migration test environment."""
    # Create a metadata file
    meta_dir = tmp_path / "processed-metadata" / "abstracts"
    meta_dir.mkdir(parents=True)
    meta_file = meta_dir / "test_painting.json"
    meta_file.write_text(json.dumps({
        "filename_base": "test_painting",
        "title": {"selected": "Test Painting"},
        "description": "A test description",
    }))

    # Create upload_status.json
    tracker_file = tmp_path / "upload_status.json"
    tracker_file.write_text(json.dumps({
        "paintings": {
            "test_painting": {
                "metadata_path": str(meta_file),
                "processed_date": "2026-02-01T10:00:00",
                "uploads": {
                    "FASO": True,
                }
            }
        },
        "platforms": ["FASO"],
        "last_updated": "2026-02-01T10:00:00"
    }))

    return tmp_path, tracker_file, meta_file


class TestMigration:
    def test_adds_gallery_sites(self, migration_env):
        _, tracker_file, meta_file = migration_env
        migrate(tracker_path=tracker_file)

        with open(meta_file) as f:
            metadata = json.load(f)

        assert "gallery_sites" in metadata
        assert "faso" in metadata["gallery_sites"]

    def test_adds_social_media(self, migration_env):
        _, tracker_file, meta_file = migration_env
        migrate(tracker_path=tracker_file)

        with open(meta_file) as f:
            metadata = json.load(f)

        assert "social_media" in metadata
        assert "mastodon" in metadata["social_media"]
        assert metadata["social_media"]["mastodon"]["post_count"] == 0
        assert metadata["social_media"]["mastodon"]["last_posted"] is None

    def test_preserves_faso_status(self, migration_env):
        _, tracker_file, meta_file = migration_env
        migrate(tracker_path=tracker_file)

        with open(meta_file) as f:
            metadata = json.load(f)

        # FASO was True in upload_status.json, so last_uploaded should be set
        assert metadata["gallery_sites"]["faso"]["last_uploaded"] is not None

    def test_creates_backup(self, migration_env):
        _, tracker_file, _ = migration_env
        migrate(tracker_path=tracker_file)

        backup = tracker_file.with_suffix(".json.bak")
        assert backup.exists()

    def test_no_tracker_file(self, tmp_path):
        # Should not crash if no upload_status.json exists
        migrate(tracker_path=tmp_path / "nonexistent.json")

    def test_dry_run(self, migration_env):
        _, tracker_file, meta_file = migration_env
        migrate(tracker_path=tracker_file, dry_run=True)

        # Metadata should NOT be modified in dry run
        with open(meta_file) as f:
            metadata = json.load(f)
        assert "gallery_sites" not in metadata
        assert "social_media" not in metadata

    def test_missing_metadata_file(self, tmp_path):
        """Paintings with missing metadata files should be skipped."""
        tracker_file = tmp_path / "upload_status.json"
        tracker_file.write_text(json.dumps({
            "paintings": {
                "missing_painting": {
                    "metadata_path": "/nonexistent/path.json",
                    "processed_date": "2026-02-01T10:00:00",
                    "uploads": {"FASO": False}
                }
            },
            "platforms": ["FASO"],
        }))
        # Should not crash
        migrate(tracker_path=tracker_file)

    def test_preserves_existing_fields(self, migration_env):
        """Migration should not overwrite existing metadata fields."""
        _, tracker_file, meta_file = migration_env
        migrate(tracker_path=tracker_file)

        with open(meta_file) as f:
            metadata = json.load(f)

        assert metadata["title"]["selected"] == "Test Painting"
        assert metadata["description"] == "A test description"
