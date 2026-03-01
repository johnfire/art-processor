"""Tests for FASO uploader helper methods (no browser needed)."""

import pytest
from pathlib import Path

from src.app.galleries.faso_uploader import FASOUploader


class TestMarkdownToHtml:
    """Test markdown to HTML conversion."""

    def test_bold(self):
        result = FASOUploader.markdown_to_html("**Bold text** here")
        assert "<strong>Bold text</strong>" in result

    def test_italic(self):
        result = FASOUploader.markdown_to_html("*Italic text* here")
        assert "<em>Italic text</em>" in result

    def test_paragraphs(self):
        result = FASOUploader.markdown_to_html("First paragraph.\n\nSecond paragraph.")
        assert "<p>First paragraph.</p>" in result
        assert "<p>Second paragraph.</p>" in result

    def test_bold_and_paragraphs(self):
        result = FASOUploader.markdown_to_html(
            "**Title** is bold.\n\nSecond paragraph here."
        )
        assert "<strong>Title</strong>" in result
        assert result.count("<p>") == 2

    def test_empty_string(self):
        assert FASOUploader.markdown_to_html("") == ""

    def test_none_handling(self):
        assert FASOUploader.markdown_to_html(None) == ""

    def test_no_markdown(self):
        result = FASOUploader.markdown_to_html("Plain text only")
        assert "<p>Plain text only</p>" in result


class TestGetImagePath:
    """Test image path extraction from metadata."""

    def test_string_path(self):
        metadata = {"files": {"big": "/path/to/image.jpg"}}
        assert FASOUploader.get_image_path(metadata) == "/path/to/image.jpg"

    def test_list_path(self):
        metadata = {"files": {"big": ["/path/to/img1.jpg", "/path/to/img2.jpg"]}}
        assert FASOUploader.get_image_path(metadata) == "/path/to/img1.jpg"

    def test_empty_list(self):
        metadata = {"files": {"big": []}}
        assert FASOUploader.get_image_path(metadata) is None

    def test_none_path(self):
        metadata = {"files": {"big": None}}
        assert FASOUploader.get_image_path(metadata) is None

    def test_missing_files_key(self):
        metadata = {}
        assert FASOUploader.get_image_path(metadata) is None

    def test_missing_big_key(self):
        metadata = {"files": {}}
        assert FASOUploader.get_image_path(metadata) is None


class TestExtractYear:
    """Test year extraction from date strings."""

    def test_full_date(self):
        assert FASOUploader.extract_year("2025-07-20") == "2025"

    def test_year_only(self):
        assert FASOUploader.extract_year("2024") == "2024"

    def test_none_returns_current_year(self):
        from datetime import datetime
        result = FASOUploader.extract_year(None)
        assert result == str(datetime.now().year)

    def test_empty_string_returns_current_year(self):
        from datetime import datetime
        result = FASOUploader.extract_year("")
        assert result == str(datetime.now().year)

    def test_short_string_returns_current_year(self):
        from datetime import datetime
        result = FASOUploader.extract_year("20")
        assert result == str(datetime.now().year)


class TestIsUploadReady:
    """Test upload readiness validation."""

    def test_complete_metadata(self, tmp_path):
        # Create a temporary image file so path check passes
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake image data")

        metadata = {
            "title": {"selected": "Test Painting"},
            "files": {"big": str(img)},
            "medium": "Acrylic",
            "substrate": "Canvas",
            "subject": "Abstract",
            "style": "Abstract",
            "collection": "Test Collection",
            "dimensions": {"width": 50.0, "height": 70.0},
            "description": "A test painting description.",
        }
        ready, missing = FASOUploader.is_upload_ready(metadata)
        assert ready is True
        assert missing == []

    def test_missing_title(self, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake")

        metadata = {
            "title": {"selected": ""},
            "files": {"big": str(img)},
            "medium": "Acrylic",
            "substrate": "Canvas",
            "subject": "Abstract",
            "style": "Abstract",
            "collection": "Test",
            "dimensions": {"width": 50.0, "height": 70.0},
            "description": "Desc.",
        }
        ready, missing = FASOUploader.is_upload_ready(metadata)
        assert ready is False
        assert "title" in missing

    def test_missing_image_path(self):
        metadata = {
            "title": {"selected": "Test"},
            "files": {"big": None},
            "medium": "Acrylic",
            "substrate": "Canvas",
            "subject": "Abstract",
            "style": "Abstract",
            "collection": "Test",
            "dimensions": {"width": 50.0, "height": 70.0},
            "description": "Desc.",
        }
        ready, missing = FASOUploader.is_upload_ready(metadata)
        assert ready is False
        assert "image file path" in missing

    def test_image_file_not_found(self):
        metadata = {
            "title": {"selected": "Test"},
            "files": {"big": "/nonexistent/path/painting.jpg"},
            "medium": "Acrylic",
            "substrate": "Canvas",
            "subject": "Abstract",
            "style": "Abstract",
            "collection": "Test",
            "dimensions": {"width": 50.0, "height": 70.0},
            "description": "Desc.",
        }
        ready, missing = FASOUploader.is_upload_ready(metadata)
        assert ready is False
        assert any("image file missing" in m for m in missing)

    def test_missing_multiple_fields(self):
        metadata = {
            "title": {"selected": "Test"},
            "files": {"big": None},
            "medium": None,
            "substrate": None,
            "dimensions": {"width": None, "height": None},
        }
        ready, missing = FASOUploader.is_upload_ready(metadata)
        assert ready is False
        assert len(missing) >= 4

    def test_list_image_path(self, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake")

        metadata = {
            "title": {"selected": "Test"},
            "files": {"big": [str(img)]},
            "medium": "Acrylic",
            "substrate": "Canvas",
            "subject": "Abstract",
            "style": "Abstract",
            "collection": "Test",
            "dimensions": {"width": 50.0, "height": 70.0},
            "description": "Desc.",
        }
        ready, missing = FASOUploader.is_upload_ready(metadata)
        assert ready is True
