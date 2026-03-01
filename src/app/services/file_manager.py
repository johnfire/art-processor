"""
File management module for handling artwork files.
Handles pairing instagram/big versions, renaming, and file operations.
"""

import re
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

from PIL import Image
from PIL.ExifTags import TAGS

from config.settings import (
    PAINTINGS_BIG_PATH,
    PAINTINGS_INSTAGRAM_PATH,
    SUPPORTED_IMAGE_FORMATS,
    SANITIZE_RULES,
)


class FileManager:
    """Manages artwork file operations."""
    
    def __init__(self):
        """Initialize file manager with configured paths."""
        self.big_path = PAINTINGS_BIG_PATH
        self.instagram_path = PAINTINGS_INSTAGRAM_PATH
    
    def sanitize_filename(self, title: str) -> str:
        """
        Convert artwork title to safe filename.
        
        Args:
            title: The artwork title
            
        Returns:
            Sanitized filename (without extension)
        """
        filename = title.lower()
        
        # Apply sanitization rules
        for char, replacement in SANITIZE_RULES.items():
            filename = filename.replace(char, replacement)
        
        # Remove any remaining special characters
        filename = re.sub(r'[^\w\s-]', '', filename)
        
        # Replace multiple underscores/spaces with single underscore
        filename = re.sub(r'[_\s]+', '_', filename)
        
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        
        return filename
    
    def find_painting_files(self, category: str) -> List[Tuple[Path, Path]]:
        """
        Find all painting pairs in a category.
        
        Args:
            category: Category subfolder name
            
        Returns:
            List of tuples (big_path, instagram_path) for each painting
        """
        big_category_path = self.big_path / category
        instagram_category_path = self.instagram_path / category
        
        if not big_category_path.exists():
            return []
        
        pairs = []
        
        # Find all images in big folder
        for big_file in big_category_path.iterdir():
            if big_file.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                # Look for matching instagram version
                instagram_file = instagram_category_path / big_file.name
                
                if instagram_file.exists():
                    pairs.append((big_file, instagram_file))
                else:
                    # Only big version exists
                    pairs.append((big_file, None))
        
        return pairs
    
    def get_available_categories(self) -> List[str]:
        """
        Discover all available categories from folder structure.
        
        Returns:
            List of category names
        """
        if not self.big_path.exists():
            return []
        
        categories = []
        for item in self.big_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                categories.append(item.name)
        
        return sorted(categories)
    
    def rename_painting_pair(
        self,
        big_file: Path,
        instagram_file: Optional[Path],
        new_name: str,
    ) -> Tuple[Path, Optional[Path]]:
        """
        Rename both versions of a painting.
        
        Args:
            big_file: Path to big version
            instagram_file: Path to instagram version (or None)
            new_name: New sanitized filename (without extension)
            
        Returns:
            Tuple of new paths (big_path, instagram_path)
        """
        # Handle name collision
        new_name = self._handle_collision(big_file.parent, new_name, big_file.suffix)
        
        # Rename big version
        new_big_path = big_file.parent / f"{new_name}{big_file.suffix}"
        big_file.rename(new_big_path)
        
        # Rename instagram version if it exists
        new_instagram_path = None
        if instagram_file and instagram_file.exists():
            new_instagram_path = instagram_file.parent / f"{new_name}{instagram_file.suffix}"
            instagram_file.rename(new_instagram_path)
        
        return new_big_path, new_instagram_path
    
    def _handle_collision(self, directory: Path, base_name: str, extension: str) -> str:
        """
        Handle filename collisions by appending numbers.
        
        Args:
            directory: Directory where file will be created
            base_name: Base filename without extension
            extension: File extension
            
        Returns:
            Unique filename
        """
        new_name = base_name
        counter = 1
        
        while (directory / f"{new_name}{extension}").exists():
            new_name = f"{base_name}_{counter:02d}"
            counter += 1
        
        return new_name
    
    def extract_exif_date(self, image_path: Path) -> Optional[str]:
        """
        Extract creation date from EXIF data.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Date string in YYYY-MM-DD format, or None
        """
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        # Look for DateTime or DateTimeOriginal
                        if tag in ['DateTime', 'DateTimeOriginal']:
                            # Format is usually "YYYY:MM:DD HH:MM:SS"
                            date_str = str(value).split()[0]
                            date_str = date_str.replace(':', '-')
                            return date_str
        except Exception:
            pass
        
        return None
    
    def get_file_creation_date(self, file_path: Path) -> str:
        """
        Get file creation date as fallback.
        
        Args:
            file_path: Path to file
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        timestamp = file_path.stat().st_mtime
        date = datetime.fromtimestamp(timestamp)
        return date.strftime('%Y-%m-%d')
    
    def get_creation_date(self, image_path: Path) -> str:
        """
        Get creation date from EXIF or file metadata.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        # Try EXIF first
        exif_date = self.extract_exif_date(image_path)
        if exif_date:
            return exif_date
        
        # Fall back to file creation date
        return self.get_file_creation_date(image_path)
