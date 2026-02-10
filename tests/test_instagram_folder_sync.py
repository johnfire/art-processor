"""
Unit tests for instagram_folder_sync module.
"""

import pytest
from pathlib import Path

from src.instagram_folder_sync import InstagramFolderSync


def _touch_image(folder: Path, name: str):
    """Helper to create a dummy image file."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).touch()


@pytest.mark.unit
class TestFlattenInstagram:
    """Test flattening instagram subfolders to root."""

    def test_moves_files_to_root(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        _touch_image(ig / "abstracts", "painting-a.jpg")
        _touch_image(ig / "landscapes", "painting-b.jpg")

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        moved, warnings = syncer.flatten_instagram()

        assert moved == 2
        assert (ig / "painting-a.jpg").exists()
        assert (ig / "painting-b.jpg").exists()

    def test_deletes_empty_subfolders(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        _touch_image(ig / "abstracts", "painting.jpg")

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        syncer.flatten_instagram()

        assert not (ig / "abstracts").exists()

    def test_handles_filename_collision(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        # Same filename in two subfolders
        _touch_image(ig / "folder-a", "duplicate.jpg")
        _touch_image(ig / "folder-b", "duplicate.jpg")

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        moved, warnings = syncer.flatten_instagram()

        assert moved == 2
        assert (ig / "duplicate.jpg").exists()
        assert (ig / "duplicate_1.jpg").exists()
        assert len(warnings) == 1
        assert "collision" in warnings[0]

    def test_skips_non_image_files(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        _touch_image(ig / "stuff", "painting.jpg")
        (ig / "stuff" / "readme.txt").touch()

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        moved, warnings = syncer.flatten_instagram()

        assert moved == 1
        assert (ig / "painting.jpg").exists()
        # txt file stays in subfolder, so subfolder not deleted
        assert (ig / "stuff" / "readme.txt").exists()

    def test_skips_hidden_folders(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        _touch_image(ig / ".hidden", "secret.jpg")

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        moved, warnings = syncer.flatten_instagram()

        assert moved == 0

    def test_nonexistent_instagram_path(self, tmp_path):
        syncer = InstagramFolderSync(
            big_path=tmp_path / "big",
            instagram_path=tmp_path / "nonexistent",
        )
        moved, warnings = syncer.flatten_instagram()

        assert moved == 0
        assert len(warnings) == 1


@pytest.mark.unit
class TestEnsureSubfolders:
    """Test creating matching subfolders."""

    def test_creates_missing_subfolders(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        (big / "abstracts").mkdir()
        (big / "landscapes").mkdir()

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        created = syncer.ensure_subfolders()

        assert len(created) == 2
        assert (ig / "abstracts").exists()
        assert (ig / "landscapes").exists()

    def test_skips_existing_subfolders(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        (big / "abstracts").mkdir()
        (ig / "abstracts").mkdir()

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        created = syncer.ensure_subfolders()

        assert len(created) == 0


@pytest.mark.unit
class TestMatchAndMove:
    """Test matching and moving files."""

    def test_matches_by_filename(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        # Big has organized files
        _touch_image(big / "landscapes", "sunset.jpg")
        _touch_image(big / "landscapes", "river.jpg")

        # Instagram has matching files in root
        _touch_image(ig, "sunset.jpg")
        _touch_image(ig, "river.jpg")
        (ig / "landscapes").mkdir()

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        result = syncer.match_and_move()

        assert result["total_matched"] == 2
        assert (ig / "landscapes" / "sunset.jpg").exists()
        assert (ig / "landscapes" / "river.jpg").exists()
        assert not (ig / "sunset.jpg").exists()
        assert not (ig / "river.jpg").exists()

    def test_unmatched_big_files_warned(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        _touch_image(big / "landscapes", "no-match.jpg")

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        result = syncer.match_and_move()

        assert result["total_unmatched"] == 1
        assert "landscapes/no-match.jpg" in result["unmatched_big"]

    def test_leftover_instagram_files(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        (big / "landscapes").mkdir()
        _touch_image(ig, "orphan.jpg")

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        result = syncer.match_and_move()

        assert "orphan.jpg" in result["leftover_instagram"]
        assert (ig / "orphan.jpg").exists()

    def test_case_insensitive_matching(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        _touch_image(big / "landscapes", "Sunset.JPG")
        _touch_image(ig, "sunset.jpg")
        (ig / "landscapes").mkdir()

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        result = syncer.match_and_move()

        # Case-insensitive match: big has "Sunset.JPG", instagram has "sunset.jpg"
        # The key is .lower() so "sunset.jpg" matches "sunset.jpg"
        assert result["total_matched"] == 1


@pytest.mark.unit
class TestFullSync:
    """End-to-end sync tests."""

    def test_full_sync_workflow(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        # Big structure
        _touch_image(big / "landscapes", "mountain.jpg")
        _touch_image(big / "landscapes", "river.jpg")
        _touch_image(big / "abstracts", "swirl.jpg")

        # Instagram: files in wrong folders
        _touch_image(ig / "old-folder", "mountain.jpg")
        _touch_image(ig / "misc", "river.jpg")
        _touch_image(ig / "misc", "swirl.jpg")
        _touch_image(ig / "misc", "orphan.jpg")

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        result = syncer.sync()

        # All 4 files moved out of subfolders
        assert result["flatten_moved"] == 4

        # Subfolders created to match big
        assert "landscapes" in result["created_folders"] or (ig / "landscapes").exists()
        assert "abstracts" in result["created_folders"] or (ig / "abstracts").exists()

        # 3 matched and moved
        assert result["total_matched"] == 3
        assert (ig / "landscapes" / "mountain.jpg").exists()
        assert (ig / "landscapes" / "river.jpg").exists()
        assert (ig / "abstracts" / "swirl.jpg").exists()

        # 1 leftover
        assert "orphan.jpg" in result["leftover_instagram"]
        assert (ig / "orphan.jpg").exists()

    def test_sync_with_empty_directories(self, tmp_path):
        big = tmp_path / "big"
        ig = tmp_path / "instagram"
        big.mkdir()
        ig.mkdir()

        syncer = InstagramFolderSync(big_path=big, instagram_path=ig)
        result = syncer.sync()

        assert result["flatten_moved"] == 0
        assert result["total_matched"] == 0
