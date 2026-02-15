"""Tests for social media post text formatter."""

import pytest
from urllib.parse import urlparse
from src.social.formatter import (
    format_post_text,
    truncate_description,
    subject_to_hashtag,
    build_hashtags,
    WEBSITE_URL,
)


class TestTruncateDescription:
    def test_short_text_unchanged(self):
        text = "A beautiful painting of a sunset."
        assert truncate_description(text, max_words=75) == text

    def test_long_text_truncated(self):
        words = ["word"] * 100
        text = " ".join(words)
        result = truncate_description(text, max_words=10)
        assert result == "word " * 9 + "word..."

    def test_exact_limit(self):
        text = "one two three four five"
        result = truncate_description(text, max_words=5)
        assert result == text  # no truncation needed

    def test_empty_string(self):
        assert truncate_description("", max_words=75) == ""

    def test_none_input(self):
        assert truncate_description(None, max_words=75) == ""

    def test_strips_bold_markdown(self):
        text = "A **bold** description with **emphasis**."
        result = truncate_description(text, max_words=75)
        assert "**" not in result
        assert "bold" in result
        assert "emphasis" in result

    def test_strips_italic_markdown(self):
        text = "An *italic* word here."
        result = truncate_description(text, max_words=75)
        assert "*" not in result
        assert "italic" in result

    def test_collapses_whitespace(self):
        text = "word   with   spaces"
        result = truncate_description(text, max_words=75)
        assert result == "word with spaces"


class TestSubjectToHashtag:
    def test_simple_subject(self):
        assert subject_to_hashtag("Abstract") == "#abstract"

    def test_multi_word_subject(self):
        assert subject_to_hashtag("Sea Beasties on Titan") == "#seabeastiesontitan"

    def test_subject_with_punctuation(self):
        assert subject_to_hashtag("Still Life!") == "#stilllife"

    def test_empty_subject(self):
        assert subject_to_hashtag("") == ""

    def test_none_subject(self):
        assert subject_to_hashtag(None) == ""


class TestBuildHashtags:
    def test_with_subject(self):
        result = build_hashtags("Abstract")
        assert result == "#art #artforsale #abstract"

    def test_without_subject(self):
        result = build_hashtags("")
        assert result == "#art #artforsale"

    def test_no_duplicate_art(self):
        # Shouldn't happen with real subjects, but ensure no duplicates
        result = build_hashtags("Landscape")
        tags = result.split()
        assert len(tags) == len(set(tags))


class TestFormatPostText:
    def test_full_metadata(self):
        metadata = {
            "title": {"selected": "Chromatic Entropy"},
            "description": "A vibrant abstract painting exploring chaos.",
            "subject": "Abstract",
        }
        result = format_post_text(metadata)
        assert "Chromatic Entropy" in result
        assert "vibrant abstract" in result
        assert "#art" in result
        assert "#artforsale" in result
        assert "#abstract" in result
        assert any(urlparse(f"https://{w}").hostname == WEBSITE_URL for w in result.split())

    def test_no_description(self):
        metadata = {
            "title": {"selected": "Test"},
            "description": None,
            "subject": "Landscape",
        }
        result = format_post_text(metadata)
        assert "Test" in result
        assert "#landscape" in result
        assert any(urlparse(f"https://{w}").hostname == WEBSITE_URL for w in result.split())

    def test_long_description_truncated(self):
        long_desc = " ".join(["word"] * 200)
        metadata = {
            "title": {"selected": "Title"},
            "description": long_desc,
            "subject": "Abstract",
        }
        result = format_post_text(metadata, max_words=10)
        # Should have title, truncated desc, hashtags
        lines = result.split("\n\n")
        assert lines[0] == "Title"

    def test_missing_title(self):
        metadata = {"title": {}, "description": "desc", "subject": "Still Life"}
        result = format_post_text(metadata)
        assert "Untitled" in result
