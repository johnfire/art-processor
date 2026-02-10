"""
Collection folder manager - ensures all collection folders exist.
"""

from pathlib import Path
from typing import List, Tuple
from rich.console import Console

console = Console()


class CollectionFolderManager:
    """Manages collection folders across painting directories."""
    
    def __init__(self, big_path: Path, instagram_path: Path, collections: List[str]):
        """
        Initialize collection folder manager.
        
        Args:
            big_path: Path to big paintings folder
            instagram_path: Path to Instagram paintings folder
            collections: List of collection names from settings
        """
        self.big_path = big_path
        self.instagram_path = instagram_path
        self.collections = collections
    
    def _sanitize_collection_name(self, collection_name: str) -> str:
        """
        Convert collection name to folder name.
        
        Args:
            collection_name: Display name (e.g., "Oil Paintings")
            
        Returns:
            Sanitized folder name (e.g., "oil-paintings")
        """
        # Lowercase
        folder_name = collection_name.lower()
        
        # Replace spaces with dashes
        folder_name = folder_name.replace(" ", "-")
        
        # Remove special characters
        import re
        folder_name = re.sub(r'[^a-z0-9\-]', '', folder_name)
        
        # Remove multiple consecutive dashes
        folder_name = re.sub(r'-+', '-', folder_name)
        
        # Remove leading/trailing dashes
        folder_name = folder_name.strip('-')
        
        return folder_name
    
    def get_existing_folders(self, base_path: Path) -> List[str]:
        """
        Get list of existing collection folders.
        
        Args:
            base_path: Path to check (big or instagram)
            
        Returns:
            List of existing folder names
        """
        if not base_path.exists():
            return []
        
        folders = []
        for item in base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                folders.append(item.name)
        
        return folders
    
    def create_missing_folders(self) -> Tuple[List[str], List[str]]:
        """
        Create any missing collection folders.
        
        Returns:
            Tuple of (created_folders, errors)
        """
        created = []
        errors = []
        
        # Ensure base directories exist
        for base_path in [self.big_path, self.instagram_path]:
            if not base_path.exists():
                try:
                    base_path.mkdir(parents=True, exist_ok=True)
                    console.print(f"[green]✓ Created base directory: {base_path}[/green]")
                except Exception as e:
                    errors.append(f"Failed to create {base_path}: {e}")
                    continue
        
        # Get existing folders
        existing_big = set(self.get_existing_folders(self.big_path))
        existing_instagram = set(self.get_existing_folders(self.instagram_path))
        
        # Process each collection
        for collection in self.collections:
            folder_name = self._sanitize_collection_name(collection)
            
            # Create in big folder if missing
            big_folder = self.big_path / folder_name
            if folder_name not in existing_big:
                try:
                    big_folder.mkdir(parents=True, exist_ok=True)
                    created.append(f"big/{folder_name}")
                    console.print(f"[green]✓ Created: {big_folder}[/green]")
                except Exception as e:
                    errors.append(f"Failed to create {big_folder}: {e}")
            
            # Create in Instagram folder if missing
            instagram_folder = self.instagram_path / folder_name
            if folder_name not in existing_instagram:
                try:
                    instagram_folder.mkdir(parents=True, exist_ok=True)
                    created.append(f"instagram/{folder_name}")
                    console.print(f"[green]✓ Created: {instagram_folder}[/green]")
                except Exception as e:
                    errors.append(f"Failed to create {instagram_folder}: {e}")
        
        return created, errors
    
    def sync_collection_folders(self) -> dict:
        """
        Ensure all collection folders exist in both directories.
        
        Returns:
            Dict with results: {
                'created': list of created folders,
                'errors': list of errors,
                'total_collections': int,
                'missing_count': int
            }
        """
        console.print("\n[bold cyan]Collection Folder Sync[/bold cyan]\n")
        console.print(f"Collections defined: {len(self.collections)}")
        console.print(f"Big paintings path: {self.big_path}")
        console.print(f"Instagram path: {self.instagram_path}\n")
        
        created, errors = self.create_missing_folders()
        
        result = {
            'created': created,
            'errors': errors,
            'total_collections': len(self.collections),
            'missing_count': len(created)
        }
        
        # Summary
        if created:
            console.print(f"\n[green]✓ Created {len(created)} folder(s)[/green]")
        else:
            console.print("\n[green]✓ All collection folders already exist[/green]")
        
        if errors:
            console.print(f"\n[red]✗ {len(errors)} error(s) occurred:[/red]")
            for error in errors:
                console.print(f"  [red]• {error}[/red]")
        
        return result


def sync_collection_folders_cli():
    """
    CLI function to sync collection folders.
    Called from admin mode.
    """
    from config.settings import (
        PAINTINGS_BIG_PATH,
        PAINTINGS_INSTAGRAM_PATH,
        COLLECTIONS
    )
    
    manager = CollectionFolderManager(
        big_path=PAINTINGS_BIG_PATH,
        instagram_path=PAINTINGS_INSTAGRAM_PATH,
        collections=COLLECTIONS
    )
    
    result = manager.sync_collection_folders()
    
    return result


if __name__ == "__main__":
    # Test/demo mode
    sync_collection_folders_cli()
