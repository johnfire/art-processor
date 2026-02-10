"""
Unit tests for metadata_editor module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from src.metadata_editor import MetadataEditor


def _create_metadata_file(folder: Path, filename_base: str, is_skeleton: bool = True, **overrides):
    """Helper to create a test metadata JSON file."""
    metadata = {
        "filename_base": filename_base,
        "category": folder.name,
        "files": {"big": [f"/path/to/{filename_base}.jpg"], "instagram": None},
        "title": {"selected": filename_base.replace("_", " ").title(), "all_options": []},
        "description": None,
        "dimensions": {"width": None, "height": None, "depth": None, "unit": None, "formatted": None},
        "substrate": None,
        "medium": None,
        "subject": None,
        "style": None,
        "collection": None,
        "price_eur": None,
        "creation_date": None,
        "processed_date": "2026-02-10T12:00:00",
        "analyzed_from": None,
        "is_skeleton": is_skeleton,
    }
    metadata.update(overrides)
    file_path = folder / f"{filename_base}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    return metadata


@pytest.mark.unit
class TestListSubfolders:
    """Test subfolder listing."""

    def test_lists_folders_with_json(self, tmp_path):
        folder_a = tmp_path / "landscapes"
        folder_a.mkdir()
        _create_metadata_file(folder_a, "mountain")

        folder_b = tmp_path / "abstracts"
        folder_b.mkdir()
        _create_metadata_file(folder_b, "swirl")

        editor = MetadataEditor(metadata_path=tmp_path)
        folders = editor.list_subfolders()

        assert len(folders) == 2
        assert "abstracts" in folders
        assert "landscapes" in folders

    def test_skips_empty_folders(self, tmp_path):
        (tmp_path / "empty-folder").mkdir()
        folder = tmp_path / "has-files"
        folder.mkdir()
        _create_metadata_file(folder, "painting")

        editor = MetadataEditor(metadata_path=tmp_path)
        folders = editor.list_subfolders()

        assert folders == ["has-files"]

    def test_skips_hidden_folders(self, tmp_path):
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        _create_metadata_file(hidden, "secret")

        editor = MetadataEditor(metadata_path=tmp_path)
        assert editor.list_subfolders() == []

    def test_nonexistent_path(self, tmp_path):
        editor = MetadataEditor(metadata_path=tmp_path / "nonexistent")
        assert editor.list_subfolders() == []


@pytest.mark.unit
class TestListMetadataFiles:
    """Test metadata file listing."""

    def test_lists_files_with_details(self, tmp_path):
        folder = tmp_path / "landscapes"
        folder.mkdir()
        _create_metadata_file(folder, "mountain_view")
        _create_metadata_file(folder, "river_bank", is_skeleton=False, substrate="Canvas")

        editor = MetadataEditor(metadata_path=tmp_path)
        files = editor.list_metadata_files("landscapes")

        assert len(files) == 2
        # Sorted alphabetically
        assert files[0] == ("mountain_view", "Mountain View", True)
        assert files[1] == ("river_bank", "River Bank", False)

    def test_empty_folder(self, tmp_path):
        folder = tmp_path / "empty"
        folder.mkdir()

        editor = MetadataEditor(metadata_path=tmp_path)
        assert editor.list_metadata_files("empty") == []


@pytest.mark.unit
class TestPromptSelect:
    """Test the generic list selector."""

    def test_keep_current_returns_current(self, tmp_path):
        editor = MetadataEditor(metadata_path=tmp_path)

        with patch("src.metadata_editor.IntPrompt.ask", return_value=0):
            result = editor._prompt_select("Medium", ["Oil", "Acrylic"], "Oil")

        assert result == "Oil"

    def test_select_new_option(self, tmp_path):
        editor = MetadataEditor(metadata_path=tmp_path)

        with patch("src.metadata_editor.IntPrompt.ask", return_value=2):
            result = editor._prompt_select("Medium", ["Oil", "Acrylic"], "Oil")

        assert result == "Acrylic"

    def test_keep_none_current(self, tmp_path):
        editor = MetadataEditor(metadata_path=tmp_path)

        with patch("src.metadata_editor.IntPrompt.ask", return_value=0):
            result = editor._prompt_select("Style", ["Abstract", "Realism"], None)

        assert result is None


@pytest.mark.unit
class TestEditFile:
    """Test the full edit flow."""

    def test_edit_saves_changes(self, tmp_path):
        folder = tmp_path / "landscapes"
        folder.mkdir()
        _create_metadata_file(folder, "mountain_view")

        editor = MetadataEditor(metadata_path=tmp_path)
        editor.metadata_mgr.output_path = tmp_path

        with patch.multiple(
            "src.metadata_editor",
            Confirm=type("MockConfirm", (), {
                "ask": staticmethod(lambda *a, **kw: True),
            }),
            Prompt=type("MockPrompt", (), {
                "ask": staticmethod(lambda *a, **kw: kw.get("default", "")),
            }),
            IntPrompt=type("MockIntPrompt", (), {
                "ask": staticmethod(lambda *a, **kw: 1),
            }),
            FloatPrompt=type("MockFloatPrompt", (), {
                "ask": staticmethod(lambda *a, **kw: 100.0),
            }),
        ):
            result = editor.edit_file("landscapes", "mountain_view")

        assert result is True

        # Verify file was saved
        with open(folder / "mountain_view.json") as f:
            data = json.load(f)

        # IntPrompt returns 1 → first option from each list
        assert data["substrate"] is not None
        assert data["medium"] is not None
        assert data["price_eur"] == 100.0

    def test_skip_file(self, tmp_path):
        folder = tmp_path / "landscapes"
        folder.mkdir()
        original = _create_metadata_file(folder, "mountain_view")

        editor = MetadataEditor(metadata_path=tmp_path)
        editor.metadata_mgr.output_path = tmp_path

        # User declines to edit
        with patch("src.metadata_editor.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = False
            result = editor.edit_file("landscapes", "mountain_view")

        assert result is False

        # File should be unchanged
        with open(folder / "mountain_view.json") as f:
            data = json.load(f)
        assert data["substrate"] is None

    def test_skeleton_flag_removed_when_complete(self, tmp_path):
        folder = tmp_path / "abstracts"
        folder.mkdir()
        _create_metadata_file(folder, "swirl")

        editor = MetadataEditor(metadata_path=tmp_path)
        editor.metadata_mgr.output_path = tmp_path

        # Mock: user fills all key fields (IntPrompt returns 1 for all selects)
        with patch.multiple(
            "src.metadata_editor",
            Confirm=type("MockConfirm", (), {
                "ask": staticmethod(lambda *a, **kw: True),
            }),
            Prompt=type("MockPrompt", (), {
                "ask": staticmethod(lambda *a, **kw: kw.get("default", "")),
            }),
            IntPrompt=type("MockIntPrompt", (), {
                "ask": staticmethod(lambda *a, **kw: 1),
            }),
            FloatPrompt=type("MockFloatPrompt", (), {
                "ask": staticmethod(lambda *a, **kw: 50.0),
            }),
        ):
            editor.edit_file("abstracts", "swirl")

        with open(folder / "swirl.json") as f:
            data = json.load(f)

        assert "is_skeleton" not in data
