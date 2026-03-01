"""
File organizer for moving processed paintings to collection-based folders.
"""

import re
import json
from pathlib import Path
from typing import Tuple, Optional

from rich.console import Console

console = Console()


class FileOrganizer:
    """Organizes processed paintings into collection-based folders."""
    
    def __init__(self, big_path: Path, instagram_path: Path, metadata_path: Path):
        """
        Initialize file organizer.
        
        Args:
            big_path: Base path for big paintings
            instagram_path: Base path for Instagram paintings
            metadata_path: Base path for metadata files
        """
        self.big_path = big_path
        self.instagram_path = instagram_path
        self.metadata_path = metadata_path
    
    def sanitize_collection_name(self, collection: str) -> str:
        """
        Convert collection name to folder-safe format.
        Lowercase and replace spaces with dashes.
        
        Args:
            collection: Collection name from metadata
            
        Returns:
            Sanitized folder name
        """
        # Convert to lowercase
        sanitized = collection.lower()
        
        # Replace spaces with dashes
        sanitized = sanitized.replace(" ", "-")
        
        # Remove any other special characters
        sanitized = re.sub(r'[^\w\-]', '', sanitized)
        
        return sanitized
    
    def organize_painting(self, filename_base: str, category: str = "new-paintings") -> Tuple[bool, str]:
        """
        Move a processed painting to its collection folder.
        
        Args:
            filename_base: Base filename without extension
            category: Current category folder (default: "new-paintings")
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Load metadata to get collection
        metadata_file = self.metadata_path / category / f"{filename_base}.json"
        
        if not metadata_file.exists():
            return False, f"Metadata not found: {metadata_file}"
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        collection = metadata.get("collection")
        if not collection:
            return False, f"No collection specified in metadata for {filename_base}"
        
        # Sanitize collection name for folder
        collection_folder = self.sanitize_collection_name(collection)
        
        # Move big version
        big_success, big_new_path = self._move_file(
            self.big_path,
            category,
            filename_base,
            collection_folder
        )
        
        if not big_success:
            return False, f"Failed to move big version: {big_new_path}"
        
        # Move Instagram version (may not exist)
        instagram_new_path = None
        instagram_old = self.instagram_path / category / f"{filename_base}.jpg"
        
        if instagram_old.exists():
            instagram_success, instagram_new_path = self._move_file(
                self.instagram_path,
                category,
                filename_base,
                collection_folder
            )
            
            if not instagram_success:
                console.print(f"[yellow]Warning: Could not move Instagram version: {instagram_new_path}[/yellow]")
        
        # Update metadata with new paths
        metadata["files"]["big"] = str(big_new_path)
        if instagram_new_path:
            metadata["files"]["instagram"] = str(instagram_new_path)
        
        metadata["collection_folder"] = collection_folder
        metadata["organized_date"] = self._get_timestamp()
        
        # Save updated metadata to new location
        new_metadata_folder = self.metadata_path / collection_folder
        new_metadata_folder.mkdir(parents=True, exist_ok=True)
        new_metadata_file = new_metadata_folder / f"{filename_base}.json"
        
        with open(new_metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update text file too
        self._update_text_metadata(metadata, collection_folder, filename_base)
        
        # Remove old metadata files
        metadata_file.unlink()
        old_txt = self.metadata_path / category / f"{filename_base}.txt"
        if old_txt.exists():
            old_txt.unlink()
        
        return True, f"Moved to {collection_folder}/"
    
    def _move_file(self, base_path: Path, from_category: str, filename_base: str, to_category: str) -> Tuple[bool, Path]:
        """
        Move a file from one category folder to another.
        
        Args:
            base_path: Base path (big or instagram)
            from_category: Source category folder
            filename_base: Filename without extension
            to_category: Destination category folder
            
        Returns:
            Tuple of (success: bool, new_path: Path)
        """
        # Find the actual file (could be .jpg or .jpeg)
        source_folder = base_path / from_category
        source_file = None
        
        for ext in ['.jpg', '.jpeg', '.png']:
            candidate = source_folder / f"{filename_base}{ext}"
            if candidate.exists():
                source_file = candidate
                break
        
        if not source_file:
            return False, Path(f"Source file not found: {filename_base}")
        
        # Create destination folder if needed
        dest_folder = base_path / to_category
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        # Move file
        dest_file = dest_folder / source_file.name
        
        try:
            source_file.rename(dest_file)
            return True, dest_file
        except Exception as e:
            return False, Path(str(e))
    
    def _update_text_metadata(self, metadata: dict, category: str, filename_base: str):
        """
        Update the human-readable text metadata file.
        
        Args:
            metadata: Metadata dictionary
            category: Category folder name
            filename_base: Base filename
        """
        from src.app.services.metadata_manager import MetadataManager
        
        mgr = MetadataManager()
        mgr.output_path = self.metadata_path
        mgr.save_metadata_text(metadata, category)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def organize_all_new_paintings(self) -> dict:
        """
        Organize all paintings in the new-paintings folder.
        
        Returns:
            Dict with success counts and errors
        """
        results = {
            "processed": 0,
            "success": 0,
            "errors": []
        }
        
        # Get all metadata files in new-paintings
        new_paintings_metadata = self.metadata_path / "new-paintings"
        
        if not new_paintings_metadata.exists():
            return results
        
        for metadata_file in new_paintings_metadata.glob("*.json"):
            filename_base = metadata_file.stem
            results["processed"] += 1
            
            success, message = self.organize_painting(filename_base, "new-paintings")
            
            if success:
                results["success"] += 1
                console.print(f"[green]✓[/green] {filename_base}: {message}")
            else:
                results["errors"].append(f"{filename_base}: {message}")
                console.print(f"[red]✗[/red] {filename_base}: {message}")
        
        return results
