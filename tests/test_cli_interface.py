"""
Unit tests for cli_interface module.
"""

import pytest
from unittest.mock import patch

from src.cli_interface import CLIInterface


@pytest.mark.unit
class TestCLIInterface:
    """Test CLIInterface class."""

    def test_init(self):
        cli = CLIInterface()
        assert cli.console is not None

    def test_select_substrate(self):
        cli = CLIInterface()
        with patch("src.cli_interface.IntPrompt.ask", return_value=1):
            result = cli.select_substrate()
        assert result == "Canvas"

    def test_select_medium(self):
        cli = CLIInterface()
        with patch("src.cli_interface.IntPrompt.ask", return_value=1):
            result = cli.select_medium()
        assert result == "Acrylic"

    def test_select_subject(self):
        cli = CLIInterface()
        with patch("src.cli_interface.IntPrompt.ask", return_value=1):
            result = cli.select_subject()
        assert result == "Abstract"

    def test_select_style(self):
        cli = CLIInterface()
        with patch("src.cli_interface.IntPrompt.ask", return_value=1):
            result = cli.select_style()
        assert result == "Abstract"

    def test_select_collection(self):
        cli = CLIInterface()
        with patch("src.cli_interface.IntPrompt.ask", return_value=1):
            result = cli.select_collection()
        assert result == "Sea Beasties from Titan"

    def test_select_title(self):
        cli = CLIInterface()
        titles = ["Title A", "Title B", "Title C", "Title D", "Title E"]
        with patch("src.cli_interface.IntPrompt.ask", return_value=3):
            result = cli.select_title(titles)
        assert result == 2  # 0-indexed

    def test_input_price(self):
        cli = CLIInterface()
        with patch("src.cli_interface.FloatPrompt.ask", return_value=150.0):
            result = cli.input_price(default=100.0)
        assert result == 150.0

    def test_input_dimensions_with_depth(self):
        cli = CLIInterface()
        with patch("src.cli_interface.FloatPrompt.ask", side_effect=[50.0, 70.0, 1.5]):
            width, height, depth, formatted = cli.input_dimensions("cm")
        assert width == 50.0
        assert height == 70.0
        assert depth == 1.5
        assert "50.0cm x 70.0cm x 1.5cm" == formatted

    def test_input_dimensions_flat(self):
        cli = CLIInterface()
        with patch("src.cli_interface.FloatPrompt.ask", side_effect=[30.0, 40.0, 0.0]):
            width, height, depth, formatted = cli.input_dimensions("in")
        assert width == 30.0
        assert height == 40.0
        assert depth is None
        assert "30.0in x 40.0in" == formatted

    def test_input_creation_date(self):
        cli = CLIInterface()
        with patch("src.cli_interface.Prompt.ask", return_value="2025-06-15"):
            result = cli.input_creation_date("2025-06-01")
        assert result == "2025-06-15"

    def test_confirm_processing(self):
        cli = CLIInterface()
        with patch("src.cli_interface.Confirm.ask", return_value=True):
            assert cli.confirm_processing("test.jpg") is True

    def test_ask_for_user_title_yes(self):
        cli = CLIInterface()
        with patch("src.cli_interface.Confirm.ask", return_value=True), \
             patch("src.cli_interface.Prompt.ask", return_value="My Title"):
            has_own, title = cli.ask_for_user_title()
        assert has_own is True
        assert title == "My Title"

    def test_ask_for_user_title_no(self):
        cli = CLIInterface()
        with patch("src.cli_interface.Confirm.ask", return_value=False):
            has_own, title = cli.ask_for_user_title()
        assert has_own is False
        assert title is None

    def test_print_success(self):
        cli = CLIInterface()
        cli.print_success("all good")

    def test_print_warning(self):
        cli = CLIInterface()
        cli.print_warning("watch out")

    def test_print_error(self):
        cli = CLIInterface()
        cli.print_error("something broke")

    def test_print_info(self):
        cli = CLIInterface()
        cli.print_info("just so you know")

    def test_select_or_custom_title_use_ai(self):
        cli = CLIInterface()
        titles = ["Title A", "Title B", "Title C"]
        with patch("src.cli_interface.Confirm.ask", return_value=True), \
             patch("src.cli_interface.IntPrompt.ask", return_value=2):
            selected, all_titles = cli.select_or_custom_title(titles)
        assert selected == "Title B"
        assert all_titles == titles

    def test_select_or_custom_title_custom(self):
        cli = CLIInterface()
        titles = ["Title A", "Title B"]
        with patch("src.cli_interface.Confirm.ask", return_value=False), \
             patch("src.cli_interface.Prompt.ask", return_value="My Own Title"):
            selected, all_titles = cli.select_or_custom_title(titles)
        assert selected == "My Own Title"
        assert all_titles == ["My Own Title"]

    def test_input_painting_notes_skip(self):
        cli = CLIInterface()
        with patch("builtins.input", return_value=""):
            result = cli.input_painting_notes()
        assert result is None

    def test_input_painting_notes_with_content(self):
        cli = CLIInterface()
        responses = iter(["Some notes about the painting", "More notes", ""])
        with patch("builtins.input", side_effect=responses):
            result = cli.input_painting_notes()
        assert result == "Some notes about the painting\nMore notes"

    def test_show_processing_summary(self):
        cli = CLIInterface()
        metadata = {
            "title": {"selected": "Test Painting"},
            "category": "test-paintings",
            "medium": "Oil",
            "dimensions": "30cm x 40cm",
            "price_eur": 100.0,
            "creation_date": "2026-01-01",
            "description": "A test painting.",
        }
        cli.show_processing_summary(metadata)  # should not raise

    def test_show_file_info_with_instagram(self, tmp_path):
        cli = CLIInterface()
        big = tmp_path / "painting.jpg"
        big.touch()
        ig = tmp_path / "painting-ig.jpg"
        ig.touch()
        cli.show_file_info(big, ig)  # should not raise

    def test_show_file_info_no_instagram(self, tmp_path):
        cli = CLIInterface()
        big = tmp_path / "painting.jpg"
        big.touch()
        cli.show_file_info(big, None)  # should not raise
