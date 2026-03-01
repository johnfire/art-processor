"""
Unit tests for upload_tracker module.
"""

import json
import pytest
from pathlib import Path

from src.app.services.upload_tracker import UploadTracker


@pytest.mark.unit
class TestUploadTracker:
    """Test UploadTracker class."""
    
    def test_initialization_new_tracker(self, temp_dir):
        """Test creating a new tracker."""
        tracker_file = temp_dir / "upload_status.json"
        tracker = UploadTracker(tracker_file)
        
        assert "paintings" in tracker.data
        assert "platforms" in tracker.data
        assert "FASO" in tracker.data["platforms"]
    
    def test_initialization_existing_tracker(self, temp_dir, mock_upload_tracker_data):
        """Test loading existing tracker."""
        tracker_file = temp_dir / "upload_status.json"
        
        # Create existing tracker
        with open(tracker_file, 'w') as f:
            json.dump(mock_upload_tracker_data, f)
        
        tracker = UploadTracker(tracker_file)
        
        assert len(tracker.data["paintings"]) == 2
        assert "test_painting_1" in tracker.data["paintings"]
    
    def test_add_painting(self, temp_dir):
        """Test adding a painting to tracker."""
        tracker_file = temp_dir / "upload_status.json"
        tracker = UploadTracker(tracker_file)
        
        tracker.add_painting("sunset_painting", "/path/to/metadata.json")
        
        assert "sunset_painting" in tracker.data["paintings"]
        assert tracker.data["paintings"]["sunset_painting"]["uploads"]["FASO"] == False
    
    def test_mark_uploaded(self, temp_dir):
        """Test marking a painting as uploaded."""
        tracker_file = temp_dir / "upload_status.json"
        tracker = UploadTracker(tracker_file)
        
        # Add and then mark as uploaded
        tracker.add_painting("test_painting", "/path/to/metadata.json")
        tracker.mark_uploaded("test_painting", "FASO")
        
        assert tracker.data["paintings"]["test_painting"]["uploads"]["FASO"] == True
    
    def test_get_pending_uploads(self, temp_dir, mock_upload_tracker_data):
        """Test getting pending uploads for a platform."""
        tracker_file = temp_dir / "upload_status.json"
        
        with open(tracker_file, 'w') as f:
            json.dump(mock_upload_tracker_data, f)
        
        tracker = UploadTracker(tracker_file)
        
        # test_painting_1: FASO=False, Instagram=False
        # test_painting_2: FASO=True, Instagram=False
        
        pending_faso = tracker.get_pending_uploads("FASO")
        pending_instagram = tracker.get_pending_uploads("Instagram")
        
        assert "test_painting_1" in pending_faso
        assert "test_painting_2" not in pending_faso
        assert len(pending_instagram) == 2
    
    def test_add_platform(self, temp_dir):
        """Test adding a new social media platform."""
        tracker_file = temp_dir / "upload_status.json"
        tracker = UploadTracker(tracker_file)
        
        # Add a painting first
        tracker.add_painting("test_painting", "/path/to/metadata.json")
        
        # Add new platform
        tracker.add_platform("Instagram")
        
        assert "Instagram" in tracker.data["platforms"]
        assert "Instagram" in tracker.data["paintings"]["test_painting"]["uploads"]
        assert tracker.data["paintings"]["test_painting"]["uploads"]["Instagram"] == False
    
    def test_get_platforms(self, temp_dir):
        """Test getting list of platforms."""
        tracker_file = temp_dir / "upload_status.json"
        tracker = UploadTracker(tracker_file)
        
        tracker.add_platform("Instagram")
        tracker.add_platform("TikTok")
        
        platforms = tracker.get_platforms()
        
        assert "FASO" in platforms
        assert "Instagram" in platforms
        assert "TikTok" in platforms
    
    def test_get_all_pending(self, temp_dir, mock_upload_tracker_data):
        """Test getting all pending uploads."""
        tracker_file = temp_dir / "upload_status.json"
        
        with open(tracker_file, 'w') as f:
            json.dump(mock_upload_tracker_data, f)
        
        tracker = UploadTracker(tracker_file)
        
        all_pending = tracker.get_all_pending()
        
        assert "FASO" in all_pending
        assert "Instagram" in all_pending
        assert len(all_pending["FASO"]) == 1  # Only test_painting_1
        assert len(all_pending["Instagram"]) == 2  # Both paintings
    
    def test_tracker_persists(self, temp_dir):
        """Test that tracker data persists to file."""
        tracker_file = temp_dir / "upload_status.json"
        
        # Create and modify tracker
        tracker1 = UploadTracker(tracker_file)
        tracker1.add_painting("test", "/path")
        
        # Load in new instance
        tracker2 = UploadTracker(tracker_file)
        
        assert "test" in tracker2.data["paintings"]


@pytest.mark.unit
def test_upload_tracker_file_creation(temp_dir):
    """Test that tracker file is created."""
    tracker_file = temp_dir / "upload_status.json"
    
    assert not tracker_file.exists()
    
    tracker = UploadTracker(tracker_file)
    tracker.add_painting("test", "/path")
    
    assert tracker_file.exists()
