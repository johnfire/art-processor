"""
Unit tests for file_organizer module.
"""

import json
import pytest
from pathlib import Path

from src.app.services.file_organizer import FileOrganizer


@pytest.mark.unit
class TestFileOrganizer:
    """Test FileOrganizer class."""
    
    def test_sanitize_collection_name(self, mock_paintings_structure):
        """Test collection name sanitization."""
        organizer = FileOrganizer(
            mock_paintings_structure["big"],
            mock_paintings_structure["instagram"],
            mock_paintings_structure["metadata"]
        )
        
        # Test various collection names
        assert organizer.sanitize_collection_name("Oil Paintings") == "oil-paintings"
        assert organizer.sanitize_collection_name("Abstract Works") == "abstract-works"
        assert organizer.sanitize_collection_name("Sea Beasties from Titan") == "sea-beasties-from-titan"
        
        # Test special characters
        assert organizer.sanitize_collection_name("Work's & Art!") == "works--art"
    
    @pytest.mark.file_ops
    def test_organize_painting(self, mock_paintings_structure, sample_image_file, sample_metadata):
        """Test organizing a single painting."""
        organizer = FileOrganizer(
            mock_paintings_structure["big"],
            mock_paintings_structure["instagram"],
            mock_paintings_structure["metadata"]
        )
        
        # Setup: Create test files
        import shutil
        
        # Create painting files
        big_file = mock_paintings_structure["big"] / "new-paintings" / "test_painting.jpg"
        instagram_file = mock_paintings_structure["instagram"] / "new-paintings" / "test_painting.jpg"
        shutil.copy(sample_image_file, big_file)
        shutil.copy(sample_image_file, instagram_file)
        
        # Create metadata file
        metadata_dir = mock_paintings_structure["metadata"] / "new-paintings"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / "test_painting.json"
        
        # Update sample metadata paths
        sample_metadata["files"]["big"] = str(big_file)
        sample_metadata["files"]["instagram"] = str(instagram_file)
        
        with open(metadata_file, 'w') as f:
            json.dump(sample_metadata, f)
        
        # Test: Organize the painting
        success, message = organizer.organize_painting("test_painting", "new-paintings")
        
        assert success
        assert "test-collection" in message.lower()
        
        # Verify: Files moved to collection folder
        expected_big = mock_paintings_structure["big"] / "test-collection" / "test_painting.jpg"
        expected_instagram = mock_paintings_structure["instagram"] / "test-collection" / "test_painting.jpg"
        
        assert expected_big.exists()
        assert expected_instagram.exists()
        
        # Verify: Original files removed
        assert not big_file.exists()
        assert not instagram_file.exists()
        
        # Verify: Metadata updated and moved
        new_metadata = mock_paintings_structure["metadata"] / "test-collection" / "test_painting.json"
        assert new_metadata.exists()
        
        with open(new_metadata, 'r') as f:
            updated_metadata = json.load(f)
        
        assert "test-collection" in updated_metadata["files"]["big"]
        assert updated_metadata.get("collection_folder") == "test-collection"
    
    @pytest.mark.file_ops
    def test_organize_painting_creates_folder(self, mock_paintings_structure, sample_image_file, sample_metadata):
        """Test that organize creates collection folder if it doesn't exist."""
        organizer = FileOrganizer(
            mock_paintings_structure["big"],
            mock_paintings_structure["instagram"],
            mock_paintings_structure["metadata"]
        )
        
        # Setup files
        import shutil
        big_file = mock_paintings_structure["big"] / "new-paintings" / "test.jpg"
        shutil.copy(sample_image_file, big_file)
        
        metadata_dir = mock_paintings_structure["metadata"] / "new-paintings"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / "test.json"
        
        sample_metadata["filename_base"] = "test"
        sample_metadata["files"]["big"] = str(big_file)
        sample_metadata["files"]["instagram"] = None
        
        with open(metadata_file, 'w') as f:
            json.dump(sample_metadata, f)
        
        # Verify collection folder doesn't exist yet
        collection_folder = mock_paintings_structure["big"] / "test-collection"
        assert not collection_folder.exists()
        
        # Organize
        success, _ = organizer.organize_painting("test", "new-paintings")
        
        assert success
        assert collection_folder.exists()
    
    def test_organize_painting_missing_metadata(self, mock_paintings_structure):
        """Test organizing with missing metadata file."""
        organizer = FileOrganizer(
            mock_paintings_structure["big"],
            mock_paintings_structure["instagram"],
            mock_paintings_structure["metadata"]
        )
        
        success, message = organizer.organize_painting("nonexistent", "new-paintings")
        
        assert not success
        assert "not found" in message.lower()
    
    def test_organize_painting_missing_collection(self, mock_paintings_structure, sample_metadata):
        """Test organizing when metadata has no collection."""
        organizer = FileOrganizer(
            mock_paintings_structure["big"],
            mock_paintings_structure["instagram"],
            mock_paintings_structure["metadata"]
        )
        
        # Create metadata without collection
        metadata_dir = mock_paintings_structure["metadata"] / "new-paintings"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / "test.json"
        
        del sample_metadata["collection"]
        
        with open(metadata_file, 'w') as f:
            json.dump(sample_metadata, f)
        
        success, message = organizer.organize_painting("test", "new-paintings")
        
        assert not success
        assert "no collection" in message.lower()


@pytest.mark.unit
def test_file_organizer_initialization(mock_paintings_structure):
    """Test FileOrganizer initializes correctly."""
    organizer = FileOrganizer(
        mock_paintings_structure["big"],
        mock_paintings_structure["instagram"],
        mock_paintings_structure["metadata"]
    )
    
    assert organizer.big_path == mock_paintings_structure["big"]
    assert organizer.instagram_path == mock_paintings_structure["instagram"]
    assert organizer.metadata_path == mock_paintings_structure["metadata"]
