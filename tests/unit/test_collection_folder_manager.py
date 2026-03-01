"""Tests for CollectionFolderManager."""

import pytest
from pathlib import Path
from unittest.mock import patch

from src.app.services.collection_folder_manager import CollectionFolderManager


@pytest.fixture
def manager(tmp_path):
    big = tmp_path / "big"
    instagram = tmp_path / "instagram"
    big.mkdir()
    instagram.mkdir()
    return CollectionFolderManager(
        big_path=big,
        instagram_path=instagram,
        collections=["Oil Paintings", "Watercolours", "Fire & Stars"],
    )


class TestSanitizeCollectionName:
    def test_lowercase(self, manager):
        assert manager._sanitize_collection_name("Oil Paintings") == "oil-paintings"

    def test_spaces_become_dashes(self, manager):
        assert manager._sanitize_collection_name("My Art Collection") == "my-art-collection"

    def test_special_chars_removed(self, manager):
        # spaces→dashes, & and ! stripped, consecutive dashes collapsed
        assert manager._sanitize_collection_name("Fire & Stars!") == "fire-stars"

    def test_multiple_dashes_collapsed(self, manager):
        assert manager._sanitize_collection_name("A  B") == "a-b"

    def test_leading_trailing_dashes_stripped(self, manager):
        assert manager._sanitize_collection_name("!Abstract!") == "abstract"

    def test_already_clean(self, manager):
        assert manager._sanitize_collection_name("landscapes") == "landscapes"


class TestGetExistingFolders:
    def test_returns_folder_names(self, manager, tmp_path):
        big = tmp_path / "big"
        (big / "landscapes").mkdir()
        (big / "portraits").mkdir()
        result = manager.get_existing_folders(big)
        assert "landscapes" in result
        assert "portraits" in result

    def test_ignores_dotfiles(self, manager, tmp_path):
        big = tmp_path / "big"
        (big / ".hidden").mkdir()
        result = manager.get_existing_folders(big)
        assert ".hidden" not in result

    def test_ignores_files(self, manager, tmp_path):
        big = tmp_path / "big"
        (big / "readme.txt").write_text("hello")
        result = manager.get_existing_folders(big)
        assert "readme.txt" not in result

    def test_nonexistent_path_returns_empty(self, manager, tmp_path):
        result = manager.get_existing_folders(tmp_path / "does_not_exist")
        assert result == []

    def test_empty_dir_returns_empty(self, manager, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        assert manager.get_existing_folders(empty) == []


class TestCreateMissingFolders:
    def test_creates_folders_in_both_dirs(self, manager, tmp_path):
        created, errors = manager.create_missing_folders()
        assert errors == []
        assert len(created) == 6  # 3 collections × 2 dirs

        for name in ["oil-paintings", "watercolours", "fire-stars"]:
            assert (tmp_path / "big" / name).exists()
            assert (tmp_path / "instagram" / name).exists()

    def test_skips_existing_folders(self, manager, tmp_path):
        (tmp_path / "big" / "oil-paintings").mkdir()
        created, errors = manager.create_missing_folders()
        # oil-paintings already exists in big, so only 5 new ones
        assert len(created) == 5

    def test_creates_base_dirs_if_missing(self, tmp_path):
        big = tmp_path / "new_big"
        instagram = tmp_path / "new_instagram"
        # Don't pre-create them
        m = CollectionFolderManager(big, instagram, ["Abstracts"])
        created, errors = m.create_missing_folders()
        assert big.exists()
        assert instagram.exists()
        assert errors == []

    def test_returns_errors_on_failure(self, tmp_path):
        big = tmp_path / "big"
        instagram = tmp_path / "instagram"
        big.mkdir()
        instagram.mkdir()

        # Make big read-only to trigger a permission error
        big.chmod(0o444)
        try:
            m = CollectionFolderManager(big, instagram, ["Test Collection"])
            created, errors = m.create_missing_folders()
            assert len(errors) > 0
        finally:
            big.chmod(0o755)  # restore so tmp_path cleanup works


class TestSyncCollectionFolders:
    def test_returns_result_dict(self, manager):
        result = manager.sync_collection_folders()
        assert "created" in result
        assert "errors" in result
        assert "total_collections" in result
        assert "missing_count" in result

    def test_total_collections_count(self, manager):
        result = manager.sync_collection_folders()
        assert result["total_collections"] == 3

    def test_creates_all_folders(self, manager, tmp_path):
        result = manager.sync_collection_folders()
        assert result["errors"] == []
        assert len(result["created"]) == 6

    def test_no_duplicates_on_second_run(self, manager):
        manager.sync_collection_folders()
        result = manager.sync_collection_folders()
        # Second run should create nothing
        assert result["created"] == []
        assert result["missing_count"] == 0
