"""
Unit tests for admin_mode module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.admin_mode import AdminMode


@pytest.fixture
def settings_file(tmp_path):
    """Create a mock settings.py file."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    settings = config_dir / "settings.py"
    settings.write_text(
        'DIMENSION_UNIT = "cm"\n\n'
        'SUBSTRATES = [\n'
        '    "Canvas",\n'
        '    "Paper",\n'
        ']\n\n'
        'MEDIUMS = [\n'
        '    "Oil",\n'
        '    "Acrylic",\n'
        ']\n\n'
        'SUBJECTS = [\n'
        '    "Abstract",\n'
        '    "Landscape",\n'
        ']\n\n'
        'STYLES = [\n'
        '    "Realism",\n'
        ']\n\n'
        'COLLECTIONS = [\n'
        '    "Oil Paintings",\n'
        ']\n'
    )
    return settings


@pytest.fixture
def env_file(tmp_path):
    """Create a mock .env file alongside settings."""
    env = tmp_path / ".env"
    env.write_text(
        "ANTHROPIC_API_KEY=sk-ant-test1234567890\n"
        "PAINTINGS_BIG_PATH=/home/test/big\n"
        "PAINTINGS_INSTAGRAM_PATH=/home/test/instagram\n"
        "METADATA_OUTPUT_PATH=/home/test/metadata\n"
    )
    return env


@pytest.fixture
def admin(settings_file):
    return AdminMode(settings_path=settings_file)


@pytest.mark.unit
class TestAdminInit:
    """Test AdminMode initialization."""

    def test_init(self, settings_file):
        admin = AdminMode(settings_path=settings_file)
        assert admin.settings_path == settings_file
        assert admin.console is not None


@pytest.mark.unit
class TestRunMenuLoop:
    """Test the main menu loop."""

    def test_exit_immediately(self, admin):
        with patch("src.admin_mode.IntPrompt.ask", return_value=0):
            admin.run()

    def test_dispatches_to_correct_method(self, admin):
        # Choose option 7 (view settings) then 0 (exit)
        with patch("src.admin_mode.IntPrompt.ask", side_effect=[7, 0]), \
             patch.object(admin, "view_current_settings") as mock_view:
            admin.run()
            mock_view.assert_called_once()


@pytest.mark.unit
class TestEditApiKey:
    """Test API key editing."""

    def test_update_existing_key(self, admin, env_file):
        with patch("src.admin_mode.Prompt.ask", return_value="sk-ant-newkey999"):
            admin.edit_api_key()

        content = env_file.read_text()
        assert "ANTHROPIC_API_KEY=sk-ant-newkey999" in content

    def test_keep_existing_key(self, admin, env_file):
        with patch("src.admin_mode.Prompt.ask", return_value=""):
            admin.edit_api_key()

        content = env_file.read_text()
        assert "ANTHROPIC_API_KEY=sk-ant-test1234567890" in content

    def test_create_env_if_missing(self, settings_file, tmp_path):
        # Remove .env
        env_path = tmp_path / ".env"
        if env_path.exists():
            env_path.unlink()

        admin = AdminMode(settings_path=settings_file)

        with patch("src.admin_mode.Confirm.ask", return_value=True), \
             patch("src.admin_mode.Prompt.ask", return_value="sk-ant-brand-new"):
            admin.edit_api_key()

        assert env_path.exists()
        assert "ANTHROPIC_API_KEY=sk-ant-brand-new" in env_path.read_text()

    def test_no_create_env_if_declined(self, settings_file, tmp_path):
        env_path = tmp_path / ".env"
        if env_path.exists():
            env_path.unlink()

        admin = AdminMode(settings_path=settings_file)

        with patch("src.admin_mode.Confirm.ask", return_value=False):
            admin.edit_api_key()

        assert not env_path.exists()


@pytest.mark.unit
class TestEditFilePaths:
    """Test file path editing."""

    def test_update_path(self, admin, env_file):
        # Update only the first path, keep others
        with patch("src.admin_mode.Prompt.ask", side_effect=["/new/big", "", ""]):
            admin.edit_file_paths()

        content = env_file.read_text()
        assert "PAINTINGS_BIG_PATH=/new/big" in content
        assert "PAINTINGS_INSTAGRAM_PATH=/home/test/instagram" in content

    def test_no_changes(self, admin, env_file):
        original = env_file.read_text()

        with patch("src.admin_mode.Prompt.ask", return_value=""):
            admin.edit_file_paths()

        assert env_file.read_text() == original

    def test_missing_env_file(self, settings_file, tmp_path):
        env_path = tmp_path / ".env"
        if env_path.exists():
            env_path.unlink()

        admin = AdminMode(settings_path=settings_file)
        # Should not raise, just prints error
        admin.edit_file_paths()


@pytest.mark.unit
class TestEditDimensionUnit:
    """Test dimension unit editing."""

    def test_switch_to_inches(self, admin, settings_file):
        with patch("src.admin_mode.IntPrompt.ask", return_value=2):
            admin.edit_dimension_unit()

        content = settings_file.read_text()
        assert 'DIMENSION_UNIT = "in"' in content

    def test_keep_cm(self, admin, settings_file):
        with patch("src.admin_mode.IntPrompt.ask", return_value=1):
            admin.edit_dimension_unit()

        content = settings_file.read_text()
        assert 'DIMENSION_UNIT = "cm"' in content


@pytest.mark.unit
class TestAddToList:
    """Test adding entries to configuration lists."""

    def test_add_substrate(self, admin, settings_file):
        with patch("src.admin_mode.Prompt.ask", side_effect=["1", "Wood"]):
            admin.add_to_list()

        content = settings_file.read_text()
        assert '"Wood"' in content

    def test_add_collection(self, admin, settings_file):
        with patch("src.admin_mode.Prompt.ask", side_effect=["5", "New Collection"]):
            admin.add_to_list()

        content = settings_file.read_text()
        assert '"New Collection"' in content

    def test_back_to_menu(self, admin, settings_file):
        original = settings_file.read_text()

        with patch("src.admin_mode.Prompt.ask", return_value="0"):
            admin.add_to_list()

        assert settings_file.read_text() == original

    def test_empty_entry(self, admin, settings_file):
        original = settings_file.read_text()

        with patch("src.admin_mode.Prompt.ask", side_effect=["1", ""]):
            admin.add_to_list()

        assert settings_file.read_text() == original


@pytest.mark.unit
class TestViewCurrentSettings:
    """Test viewing current settings."""

    def test_displays_without_error(self, admin, env_file):
        # Should not raise
        admin.view_current_settings()

    def test_displays_without_env(self, settings_file, tmp_path):
        env_path = tmp_path / ".env"
        if env_path.exists():
            env_path.unlink()

        admin = AdminMode(settings_path=settings_file)
        # Should not raise even without .env
        admin.view_current_settings()


@pytest.mark.unit
class TestWrapperMethods:
    """Test the thin wrapper methods that call into other modules."""

    def test_sync_collection_folders_declined(self, admin):
        with patch("src.admin_mode.Confirm.ask", return_value=False):
            admin.sync_collection_folders()

    def test_generate_skeleton_metadata_declined(self, admin):
        with patch("src.admin_mode.Confirm.ask", return_value=False):
            admin.generate_skeleton_metadata()

    def test_edit_metadata_calls_cli(self, admin):
        with patch("src.admin_mode.edit_metadata_cli", create=True) as mock_cli, \
             patch("src.admin_mode.Prompt.ask", return_value=""), \
             patch("src.metadata_editor.edit_metadata_cli", return_value=None):
            admin.edit_metadata()

    def test_sync_instagram_calls_cli(self, admin):
        with patch("src.instagram_folder_sync.sync_instagram_folders_cli", return_value={}), \
             patch("src.admin_mode.Prompt.ask", return_value=""):
            admin.sync_instagram_folders()
