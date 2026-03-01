"""Tests for src/galleries/__init__.py — registry functions."""

import pytest

from src.app.galleries import get_gallery, get_all_gallery_names
from src.app.galleries.base import GalleryPlatform


class TestGetAllGalleryNames:
    def test_returns_list(self):
        assert isinstance(get_all_gallery_names(), list)

    def test_contains_faso(self):
        assert "faso" in get_all_gallery_names()

    def test_returns_copy(self):
        names = get_all_gallery_names()
        names.clear()
        assert "faso" in get_all_gallery_names()


class TestGetGallery:
    def test_unknown_name_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown gallery platform"):
            get_gallery("does_not_exist")

    def test_faso_returns_gallery_platform_instance(self):
        gallery = get_gallery("faso")
        assert isinstance(gallery, GalleryPlatform)

    def test_faso_name_attribute(self):
        assert get_gallery("faso").name == "faso"

    def test_faso_display_name(self):
        assert get_gallery("faso").display_name == "FASO"

    def test_returns_new_instance_each_call(self):
        assert get_gallery("faso") is not get_gallery("faso")

    def test_empty_string_raises_key_error(self):
        with pytest.raises(KeyError):
            get_gallery("")
