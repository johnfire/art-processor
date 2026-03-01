"""
Upload tracker for managing social media and FASO upload status.
Tracks which paintings have been uploaded to which platforms.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class UploadTracker:
    """Manages upload status tracking for paintings across platforms."""
    
    def __init__(self, tracker_file: Path = None):
        """
        Initialize upload tracker.
        
        Args:
            tracker_file: Path to upload_status.json file
                         If None, uses UPLOAD_TRACKER_PATH from settings
        """
        if tracker_file is None:
            from config.settings import UPLOAD_TRACKER_PATH
            tracker_file = UPLOAD_TRACKER_PATH
            
        self.tracker_file = tracker_file
        self.data = self._load_tracker()
    
    def _load_tracker(self) -> Dict:
        """Load existing tracker data or create new."""
        if self.tracker_file.exists():
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "paintings": {},
                "platforms": ["FASO"],  # Start with FASO, user can add more
                "last_updated": None
            }
    
    def _save_tracker(self):
        """Save tracker data to file."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.tracker_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_painting(self, filename: str, metadata_path: str):
        """
        Add a newly processed painting to tracker.
        
        Args:
            filename: Base filename of painting
            metadata_path: Path to metadata file
        """
        if filename not in self.data["paintings"]:
            # Initialize with all platforms set to False (not uploaded)
            upload_status = {platform: False for platform in self.data["platforms"]}
            
            self.data["paintings"][filename] = {
                "metadata_path": str(metadata_path),
                "processed_date": datetime.now().isoformat(),
                "uploads": upload_status
            }
            self._save_tracker()
    
    def mark_uploaded(self, filename: str, platform: str):
        """
        Mark a painting as uploaded to a platform.
        
        Args:
            filename: Base filename of painting
            platform: Platform name (e.g., "FASO", "Instagram")
        """
        if filename in self.data["paintings"]:
            if platform not in self.data["paintings"][filename]["uploads"]:
                self.data["paintings"][filename]["uploads"][platform] = False
            
            self.data["paintings"][filename]["uploads"][platform] = True
            self._save_tracker()
    
    def get_pending_uploads(self, platform: str) -> List[str]:
        """
        Get list of paintings not yet uploaded to a platform.
        
        Args:
            platform: Platform name
            
        Returns:
            List of filenames pending upload
        """
        pending = []
        for filename, data in self.data["paintings"].items():
            if platform not in data["uploads"] or not data["uploads"][platform]:
                pending.append(filename)
        return pending
    
    def add_platform(self, platform_name: str):
        """
        Add a new social media platform to track.
        
        Args:
            platform_name: Name of platform (e.g., "Instagram", "Mastodon")
        """
        if platform_name not in self.data["platforms"]:
            self.data["platforms"].append(platform_name)
            
            # Add platform to all existing paintings with status False
            for painting_data in self.data["paintings"].values():
                if platform_name not in painting_data["uploads"]:
                    painting_data["uploads"][platform_name] = False
            
            self._save_tracker()
    
    def get_platforms(self) -> List[str]:
        """Get list of tracked platforms."""
        return self.data["platforms"]
    
    def get_all_pending(self) -> Dict[str, List[str]]:
        """
        Get all pending uploads organized by platform.
        
        Returns:
            Dict mapping platform names to lists of pending filenames
        """
        pending = {}
        for platform in self.data["platforms"]:
            pending[platform] = self.get_pending_uploads(platform)
        return pending
