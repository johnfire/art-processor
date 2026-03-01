"""
Unit tests for skeleton_metadata_generator module.
"""

import json
import pytest
from pathlib import Path

from src.app.services.skeleton_metadata_generator import SkeletonMetadataGenerator


@pytest.mark.unit
class TestExtractBaseName:
    """Test the base name extraction logic."""

    def test_simple_numbered(self):
        assert SkeletonMetadataGenerator.extract_base_name("Black-Palm-1") == "Black-Palm"
        assert SkeletonMetadataGenerator.extract_base_name("Black-Palm-5") == "Black-Palm"

    def test_multi_digit_number(self):
        assert SkeletonMetadataGenerator.extract_base_name("Sea-Beasties-20") == "Sea-Beasties"

    def test_no_number(self):
        assert SkeletonMetadataGenerator.extract_base_name("Fire-Star") == "Fire-Star"
        assert SkeletonMetadataGenerator.extract_base_name("In-the-Trench") == "In-the-Trench"

    def test_alphanumeric_suffix_not_stripped(self):
        assert SkeletonMetadataGenerator.extract_base_name("QBits-5-A17") == "QBits-5-A17"
        assert SkeletonMetadataGenerator.extract_base_name("Jungle-Patrol-1-A19") == "Jungle-Patrol-1-A19"

    def test_underscore_names(self):
        assert SkeletonMetadataGenerator.extract_base_name("fractured_networks") == "fractured_networks"
        assert SkeletonMetadataGenerator.extract_base_name("chromatic_entropy") == "chromatic_entropy"

    def test_single_word(self):
        assert SkeletonMetadataGenerator.extract_base_name("Trurl") == "Trurl"


@pytest.mark.unit
class TestFilenameToTitle:
    """Test filename-to-title conversion."""

    def test_dash_separated(self):
        assert SkeletonMetadataGenerator.filename_to_title("mountain-sunset") == "Mountain Sunset"

    def test_underscore_separated(self):
        assert SkeletonMetadataGenerator.filename_to_title("fractured_networks") == "Fractured Networks"

    def test_mixed_case_dashes(self):
        assert SkeletonMetadataGenerator.filename_to_title("Black-Palm") == "Black Palm"

    def test_single_word(self):
        assert SkeletonMetadataGenerator.filename_to_title("Trurl") == "Trurl"

    def test_multiple_separators(self):
        assert SkeletonMetadataGenerator.filename_to_title("The-Beach-at-Scheveningen") == "The Beach At Scheveningen"


@pytest.mark.unit
class TestScanFolder:
    """Test folder scanning and grouping."""

    def test_groups_numbered_files(self, tmp_path):
        folder = tmp_path / "test-category"
        folder.mkdir()
        (folder / "Mountain-Sunset-1.jpg").touch()
        (folder / "Mountain-Sunset-2.jpg").touch()
        (folder / "Mountain-Sunset-3.jpg").touch()
        (folder / "Standalone.jpg").touch()

        gen = SkeletonMetadataGenerator(big_path=tmp_path, metadata_path=tmp_path / "meta")
        groups = gen.scan_folder(folder)

        assert len(groups) == 2
        assert len(groups["mountain-sunset"]) == 3
        assert len(groups["standalone"]) == 1

    def test_case_insensitive_grouping(self, tmp_path):
        folder = tmp_path / "test-category"
        folder.mkdir()
        (folder / "heavens-Bell-1.jpg").touch()
        (folder / "Heavens-Bell-2.jpg").touch()

        gen = SkeletonMetadataGenerator(big_path=tmp_path, metadata_path=tmp_path / "meta")
        groups = gen.scan_folder(folder)

        assert len(groups) == 1
        assert len(groups["heavens-bell"]) == 2

    def test_skips_non_image_files(self, tmp_path):
        folder = tmp_path / "test-category"
        folder.mkdir()
        (folder / "readme.txt").touch()
        (folder / "painting.jpg").touch()

        gen = SkeletonMetadataGenerator(big_path=tmp_path, metadata_path=tmp_path / "meta")
        groups = gen.scan_folder(folder)

        assert len(groups) == 1
        assert "painting" in groups

    def test_skips_subdirectories(self, tmp_path):
        folder = tmp_path / "test-category"
        folder.mkdir()
        (folder / "unfinished").mkdir()
        (folder / "painting.jpg").touch()

        gen = SkeletonMetadataGenerator(big_path=tmp_path, metadata_path=tmp_path / "meta")
        groups = gen.scan_folder(folder)

        assert len(groups) == 1

    def test_supports_multiple_image_formats(self, tmp_path):
        folder = tmp_path / "test-category"
        folder.mkdir()
        (folder / "photo1.jpg").touch()
        (folder / "photo2.jpeg").touch()
        (folder / "photo3.png").touch()

        gen = SkeletonMetadataGenerator(big_path=tmp_path, metadata_path=tmp_path / "meta")
        groups = gen.scan_folder(folder)

        assert len(groups) == 3


@pytest.mark.unit
class TestGenerateAll:
    """Integration tests for the full generation pipeline."""

    def test_creates_skeleton_metadata(self, tmp_path):
        big = tmp_path / "big"
        meta = tmp_path / "meta"
        big.mkdir()
        meta.mkdir()

        category = big / "landscapes"
        category.mkdir()
        (category / "Mountain-View-1.jpg").touch()
        (category / "Mountain-View-2.jpg").touch()

        gen = SkeletonMetadataGenerator(big_path=big, metadata_path=meta)
        gen.metadata_mgr.output_path = meta
        result = gen.generate_all()

        assert result["total_created"] == 1
        assert result["total_skipped"] == 0

        json_path = meta / "landscapes" / "mountain_view.json"
        assert json_path.exists()

        with open(json_path) as f:
            data = json.load(f)

        assert data["title"]["selected"] == "Mountain View"
        assert data["is_skeleton"] is True
        assert data["files"]["instagram"] is None
        assert len(data["files"]["big"]) == 2
        assert data["description"] is None
        assert data["substrate"] is None

    def test_skips_existing_metadata(self, tmp_path):
        big = tmp_path / "big"
        meta = tmp_path / "meta"
        big.mkdir()
        meta.mkdir()

        category = big / "landscapes"
        category.mkdir()
        (category / "Mountain-View-1.jpg").touch()

        # Pre-create metadata
        meta_cat = meta / "landscapes"
        meta_cat.mkdir()
        with open(meta_cat / "mountain_view.json", "w") as f:
            json.dump({"filename_base": "mountain_view"}, f)

        gen = SkeletonMetadataGenerator(big_path=big, metadata_path=meta)
        gen.metadata_mgr.output_path = meta
        result = gen.generate_all()

        assert result["total_created"] == 0
        assert result["total_skipped"] == 1

    def test_single_file_creates_single_element_list(self, tmp_path):
        big = tmp_path / "big"
        meta = tmp_path / "meta"
        big.mkdir()
        meta.mkdir()

        category = big / "abstracts"
        category.mkdir()
        (category / "Fire-Star.jpg").touch()

        gen = SkeletonMetadataGenerator(big_path=big, metadata_path=meta)
        gen.metadata_mgr.output_path = meta
        result = gen.generate_all()

        assert result["total_created"] == 1

        json_path = meta / "abstracts" / "fire_star.json"
        with open(json_path) as f:
            data = json.load(f)

        assert len(data["files"]["big"]) == 1

    def test_skips_hidden_folders(self, tmp_path):
        big = tmp_path / "big"
        meta = tmp_path / "meta"
        big.mkdir()
        meta.mkdir()

        (big / ".hidden").mkdir()
        (big / ".hidden" / "secret.jpg").touch()
        category = big / "visible"
        category.mkdir()
        (category / "painting.jpg").touch()

        gen = SkeletonMetadataGenerator(big_path=big, metadata_path=meta)
        gen.metadata_mgr.output_path = meta
        result = gen.generate_all()

        assert result["total_created"] == 1
        assert len(result["folders"]) == 1
        assert result["folders"][0]["folder"] == "visible"

    def test_nonexistent_paintings_path(self, tmp_path):
        gen = SkeletonMetadataGenerator(
            big_path=tmp_path / "nonexistent",
            metadata_path=tmp_path / "meta",
        )
        result = gen.generate_all()

        assert result["total_created"] == 0
        assert len(result["errors"]) == 1

    def test_multiple_folders(self, tmp_path):
        big = tmp_path / "big"
        meta = tmp_path / "meta"
        big.mkdir()
        meta.mkdir()

        for folder_name in ["landscapes", "abstracts", "portraits"]:
            folder = big / folder_name
            folder.mkdir()
            (folder / f"Painting-{folder_name}.jpg").touch()

        gen = SkeletonMetadataGenerator(big_path=big, metadata_path=meta)
        gen.metadata_mgr.output_path = meta
        result = gen.generate_all()

        assert result["total_created"] == 3
        assert len(result["folders"]) == 3
