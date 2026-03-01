"""
Unit tests for file_manager module.
"""

import pytest
from pathlib import Path

from src.app.services.file_manager import FileManager


@pytest.mark.unit
class TestFileManager:
    """Test FileManager class."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        fm = FileManager()
        
        # Test basic sanitization
        assert fm.sanitize_filename("Simple Title") == "simple_title"
        assert fm.sanitize_filename("Title: With Colon") == "title_with_colon"
        assert fm.sanitize_filename("Multiple   Spaces") == "multiple_spaces"
        
        # Test special characters
        assert fm.sanitize_filename("Title/With\\Slash") == "title_with_slash"
        assert fm.sanitize_filename("Title?!") == "title"
        
        # Test leading/trailing underscores
        assert fm.sanitize_filename("  Spaces  ") == "spaces"
    
    def test_get_available_categories(self, mock_paintings_structure):
        """Test category discovery."""
        fm = FileManager()
        fm.big_path = mock_paintings_structure["big"]
        
        # Create some category folders
        (fm.big_path / "landscapes").mkdir()
        (fm.big_path / "abstracts").mkdir()
        
        categories = fm.get_available_categories()
        
        assert "new-paintings" in categories
        assert "landscapes" in categories
        assert "abstracts" in categories
    
    def test_find_painting_files(self, mock_paintings_structure, sample_image_file):
        """Test finding painting file pairs."""
        fm = FileManager()
        fm.big_path = mock_paintings_structure["big"]
        fm.instagram_path = mock_paintings_structure["instagram"]
        
        # Create test files
        big_folder = fm.big_path / "new-paintings"
        instagram_folder = fm.instagram_path / "new-paintings"
        
        # Copy sample image to both folders
        import shutil
        big_file = big_folder / "test001.jpg"
        instagram_file = instagram_folder / "test001.jpg"
        
        shutil.copy(sample_image_file, big_file)
        shutil.copy(sample_image_file, instagram_file)
        
        # Find pairs
        pairs = fm.find_painting_files("new-paintings")
        
        assert len(pairs) == 1
        assert pairs[0][0].name == "test001.jpg"
        assert pairs[0][1].name == "test001.jpg"
    
    def test_rename_painting_pair(self, mock_paintings_structure, sample_image_file):
        """Test renaming painting pairs."""
        fm = FileManager()
        fm.big_path = mock_paintings_structure["big"]
        fm.instagram_path = mock_paintings_structure["instagram"]
        
        # Setup test files
        import shutil
        big_folder = fm.big_path / "new-paintings"
        instagram_folder = fm.instagram_path / "new-paintings"
        
        big_file = big_folder / "test001.jpg"
        instagram_file = instagram_folder / "test001.jpg"
        
        shutil.copy(sample_image_file, big_file)
        shutil.copy(sample_image_file, instagram_file)
        
        # Rename
        new_big, new_instagram = fm.rename_painting_pair(
            big_file,
            instagram_file,
            "beautiful_sunset"
        )
        
        # Check files were renamed
        assert new_big.exists()
        assert new_big.name == "beautiful_sunset.jpg"
        assert new_instagram.exists()
        assert new_instagram.name == "beautiful_sunset.jpg"
        
        # Check old files don't exist
        assert not big_file.exists()
        assert not instagram_file.exists()
    
    def test_get_creation_date(self, sample_image_file):
        """Test creation date extraction."""
        fm = FileManager()
        
        # Should return a date string
        date = fm.get_creation_date(sample_image_file)
        
        assert len(date) == 10  # YYYY-MM-DD format
        assert date.count('-') == 2
    
    @pytest.mark.file_ops
    def test_handle_collision(self, mock_paintings_structure, sample_image_file):
        """Test filename collision handling."""
        fm = FileManager()
        
        # Create a file that would collide
        folder = mock_paintings_structure["big"] / "new-paintings"
        existing = folder / "sunset.jpg"
        existing.touch()
        
        # Test collision handling
        new_name = fm._handle_collision(folder, "sunset", ".jpg")
        
        assert new_name != "sunset"
        assert new_name.startswith("sunset_")


@pytest.mark.unit
def test_file_manager_initialization():
    """Test FileManager initializes correctly."""
    fm = FileManager()
    
    assert fm.big_path is not None
    assert fm.instagram_path is not None
