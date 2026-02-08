"""
Metadata management module.
Handles creation of JSON and text metadata files.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from config.settings import METADATA_OUTPUT_PATH


class MetadataManager:
    """Manages artwork metadata files."""
    
    def __init__(self):
        """Initialize metadata manager."""
        self.output_path = METADATA_OUTPUT_PATH
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def create_metadata(
        self,
        filename_base: str,
        category: str,
        big_file_path: Path,
        instagram_file_path: Path,
        selected_title: str,
        all_titles: List[str],
        description: str,
        width: float,
        height: float,
        depth: float,
        dimension_unit: str,
        dimensions_formatted: str,
        substrate: str,
        medium: str,
        subject: str,
        style: str,
        collection: str,
        price_eur: float,
        creation_date: str,
        analyzed_from: str = "instagram",
    ) -> Dict[str, Any]:
        """
        Create metadata dictionary.
        
        Args:
            filename_base: Base filename without extension
            category: Artwork category
            big_file_path: Path to big version
            instagram_file_path: Path to instagram version
            selected_title: The title selected by user
            all_titles: All 5 generated title options
            description: Gallery description
            width: Width value
            height: Height value
            depth: Depth value (None for flat works)
            dimension_unit: Unit of measurement ("cm" or "in")
            dimensions_formatted: Formatted dimensions string
            substrate: Substrate used (paper, canvas, etc.)
            medium: Medium used (oil, watercolor, etc.)
            subject: Subject matter
            style: Artistic style
            collection: Collection name
            price_eur: Price in euros
            creation_date: Creation date
            analyzed_from: Which version was used for AI analysis ("instagram" or "big")
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "filename_base": filename_base,
            "category": category,
            "files": {
                "big": str(big_file_path),
                "instagram": str(instagram_file_path) if instagram_file_path else None,
            },
            "title": {
                "selected": selected_title,
                "all_options": all_titles,
            },
            "description": description,
            "dimensions": {
                "width": width,
                "height": height,
                "depth": depth,
                "unit": dimension_unit,
                "formatted": dimensions_formatted,
            },
            "substrate": substrate,
            "medium": medium,
            "subject": subject,
            "style": style,
            "collection": collection,
            "price_eur": price_eur,
            "creation_date": creation_date,
            "processed_date": datetime.now().isoformat(),
            "analyzed_from": analyzed_from,
        }
        
        return metadata
    
    def save_metadata_json(self, metadata: Dict[str, Any], category: str) -> Path:
        """
        Save metadata as JSON file.
        
        Args:
            metadata: Metadata dictionary
            category: Category name for subfolder
            
        Returns:
            Path to saved JSON file
        """
        # Create category subfolder
        category_path = self.output_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        json_path = category_path / f"{metadata['filename_base']}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return json_path
    
    def save_metadata_text(self, metadata: Dict[str, Any], category: str) -> Path:
        """
        Save human-readable text version of metadata.
        
        Args:
            metadata: Metadata dictionary
            category: Category name for subfolder
            
        Returns:
            Path to saved text file
        """
        # Create category subfolder
        category_path = self.output_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Format text content
        dims = metadata.get('dimensions', {})
        if isinstance(dims, dict):
            dimensions_str = dims.get('formatted', 'N/A')
        else:
            # Backward compatibility with old format
            dimensions_str = dims
        
        text_content = f"""ARTWORK METADATA
{'=' * 60}

Title: {metadata['title']['selected']}
Category: {metadata['category']}
Subject: {metadata.get('subject', 'N/A')}
Style: {metadata.get('style', 'N/A')}
Collection: {metadata.get('collection', 'N/A')}

MATERIALS
{'-' * 60}
Substrate: {metadata.get('substrate', 'N/A')}
Medium: {metadata['medium']}

DIMENSIONS
{'-' * 60}
{dimensions_str}

Price: €{metadata['price_eur']}
Creation Date: {metadata['creation_date']}

DESCRIPTION
{'-' * 60}
{metadata['description']}

ALTERNATIVE TITLES
{'-' * 60}
"""
        
        for i, title in enumerate(metadata['title']['all_options'], 1):
            text_content += f"{i}. {title}\n"
        
        text_content += f"""
FILES
{'-' * 60}
Big Version: {metadata['files']['big']}
Instagram Version: {metadata['files']['instagram'] or 'N/A'}

PROCESSING INFO
{'-' * 60}
Processed: {metadata['processed_date']}
Analyzed From: {metadata['analyzed_from']}
"""
        
        # Save text file
        txt_path = category_path / f"{metadata['filename_base']}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        return txt_path
    
    def load_metadata(self, category: str, filename_base: str) -> Dict[str, Any]:
        """
        Load existing metadata from JSON file.
        
        Args:
            category: Category name
            filename_base: Base filename
            
        Returns:
            Metadata dictionary
        """
        json_path = self.output_path / category / f"{filename_base}.json"
        
        if not json_path.exists():
            raise FileNotFoundError(f"Metadata not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def metadata_exists(self, category: str, filename_base: str) -> bool:
        """
        Check if metadata already exists for a file.
        
        Args:
            category: Category name
            filename_base: Base filename
            
        Returns:
            True if metadata exists
        """
        json_path = self.output_path / category / f"{filename_base}.json"
        return json_path.exists()
