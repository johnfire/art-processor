"""Tests for MetadataEditor — list_subfolders and list_metadata_files."""

import json
import pytest
from pathlib import Path

from src.app.services.metadata_editor import MetadataEditor


@pytest.fixture
def editor(tmp_path):
    return MetadataEditor(metadata_path=tmp_path)


def _make_folder(base: Path, name: str, files: dict) -> Path:
    """Create a subfolder with JSON files. files = {stem: data_dict}."""
    folder = base / name
    folder.mkdir(exist_ok=True)
    for stem, data in files.items():
        (folder / f"{stem}.json").write_text(json.dumps(data))
    return folder


class TestListSubfolders:
    def test_nonexistent_path_returns_empty(self, tmp_path):
        editor = MetadataEditor(metadata_path=tmp_path / "missing")
        assert editor.list_subfolders() == []

    def test_empty_directory_returns_empty(self, editor):
        assert editor.list_subfolders() == []

    def test_folder_without_json_excluded(self, tmp_path, editor):
        (tmp_path / "landscapes").mkdir()
        assert editor.list_subfolders() == []

    def test_folder_with_json_included(self, tmp_path, editor):
        _make_folder(tmp_path, "landscapes", {"painting": {}})
        assert "landscapes" in editor.list_subfolders()

    def test_dotfolders_ignored(self, tmp_path, editor):
        _make_folder(tmp_path, ".hidden", {"p": {}})
        assert ".hidden" not in editor.list_subfolders()

    def test_files_at_top_level_ignored(self, tmp_path, editor):
        (tmp_path / "readme.txt").write_text("hello")
        assert editor.list_subfolders() == []

    def test_returns_sorted_names(self, tmp_path, editor):
        for name in ["zebra", "apple", "mango"]:
            _make_folder(tmp_path, name, {"p": {}})
        assert editor.list_subfolders() == ["apple", "mango", "zebra"]

    def test_multiple_folders(self, tmp_path, editor):
        _make_folder(tmp_path, "a", {"p": {}})
        _make_folder(tmp_path, "b", {"p": {}})
        assert editor.list_subfolders() == ["a", "b"]


class TestListMetadataFiles:
    def test_returns_three_tuple(self, tmp_path, editor):
        _make_folder(tmp_path, "landscapes", {
            "sunset": {"title": {"selected": "Sunset"}, "is_skeleton": False}
        })
        files = editor.list_metadata_files("landscapes")
        assert len(files) == 1
        filename_base, title, is_skeleton = files[0]
        assert filename_base == "sunset"
        assert title == "Sunset"
        assert is_skeleton is False

    def test_title_falls_back_to_stem(self, tmp_path, editor):
        _make_folder(tmp_path, "landscapes", {"mypainting": {}})
        _, title, _ = editor.list_metadata_files("landscapes")[0]
        assert title == "mypainting"

    def test_is_skeleton_true(self, tmp_path, editor):
        _make_folder(tmp_path, "landscapes", {
            "draft": {"title": {"selected": "Draft"}, "is_skeleton": True}
        })
        _, _, is_skeleton = editor.list_metadata_files("landscapes")[0]
        assert is_skeleton is True

    def test_is_skeleton_defaults_false(self, tmp_path, editor):
        _make_folder(tmp_path, "landscapes", {"painting": {}})
        _, _, is_skeleton = editor.list_metadata_files("landscapes")[0]
        assert is_skeleton is False

    def test_sorted_by_filename(self, tmp_path, editor):
        _make_folder(tmp_path, "landscapes", {
            "c": {"title": {"selected": "C"}},
            "a": {"title": {"selected": "A"}},
            "b": {"title": {"selected": "B"}},
        })
        names = [f[0] for f in editor.list_metadata_files("landscapes")]
        assert names == ["a", "b", "c"]

    def test_empty_folder_returns_empty(self, tmp_path, editor):
        (tmp_path / "landscapes").mkdir()
        assert editor.list_metadata_files("landscapes") == []

    def test_multiple_files(self, tmp_path, editor):
        _make_folder(tmp_path, "landscapes", {
            "one": {"title": {"selected": "One"}},
            "two": {"title": {"selected": "Two"}},
            "three": {"title": {"selected": "Three"}},
        })
        assert len(editor.list_metadata_files("landscapes")) == 3

    def test_mixed_skeleton_and_complete(self, tmp_path, editor):
        _make_folder(tmp_path, "landscapes", {
            "done": {"title": {"selected": "Done"}, "is_skeleton": False},
            "wip": {"title": {"selected": "WIP"}, "is_skeleton": True},
        })
        files = {f[0]: f[2] for f in editor.list_metadata_files("landscapes")}
        assert files["done"] is False
        assert files["wip"] is True
