"""
Image analysis module using Claude's vision capabilities.
Generates titles and descriptions for artwork.
"""

import base64
import json
from pathlib import Path
from typing import List, Dict, Any

from anthropic import Anthropic
from PIL import Image

from config.settings import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    MAX_TOKENS,
)
from config.prompts import (
    TITLE_GENERATION_PROMPT,
    DESCRIPTION_GENERATION_PROMPT,
)


class ImageAnalyzer:
    """Handles AI-powered image analysis for artwork."""
    
    def __init__(self):
        """Initialize the analyzer with Anthropic client."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL
    
    def _encode_image(self, image_path: Path) -> str:
        """
        Encode image to base64 string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def _get_image_media_type(self, image_path: Path) -> str:
        """
        Determine the media type of the image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Media type string (e.g., 'image/jpeg')
        """
        suffix = image_path.suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        return media_types.get(suffix, "image/jpeg")
    
    def generate_titles(self, image_path: Path) -> List[str]:
        """
        Generate 5 diverse title options for an artwork.
        
        Args:
            image_path: Path to the artwork image
            
        Returns:
            List of 5 title strings
        """
        print(f"  → Analyzing image for title generation...")
        
        # Encode image
        image_data = self._encode_image(image_path)
        media_type = self._get_image_media_type(image_path)
        
        # Call Claude API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": TITLE_GENERATION_PROMPT,
                        },
                    ],
                }
            ],
        )
        
        # Parse response
        response_text = message.content[0].text
        
        # Extract JSON from response
        try:
            titles = json.loads(response_text)
            if isinstance(titles, list) and len(titles) == 5:
                return titles
            else:
                raise ValueError("Response is not a list of 5 titles")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ⚠ Warning: Could not parse titles as JSON: {e}")
            print(f"  Raw response: {response_text}")
            # Fallback: try to extract titles from text
            return self._extract_titles_from_text(response_text)
    
    def _extract_titles_from_text(self, text: str) -> List[str]:
        """
        Fallback method to extract titles from non-JSON response.
        
        Args:
            text: Raw text response
            
        Returns:
            List of extracted titles
        """
        # Simple heuristic: look for quoted strings
        import re
        matches = re.findall(r'"([^"]+)"', text)
        if len(matches) >= 5:
            return matches[:5]
        
        # If that fails, split by lines and take first 5 non-empty
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return lines[:5] if len(lines) >= 5 else lines + ["Untitled"] * (5 - len(lines))
    
    def generate_description(
        self,
        image_path: Path,
        title: str,
        medium: str,
        dimensions: str,
        category: str,
    ) -> str:
        """
        Generate a gallery-quality description for an artwork.
        
        Args:
            image_path: Path to the artwork image
            title: Selected title for the artwork
            medium: Medium used (e.g., "Oil on canvas")
            dimensions: Dimensions string (e.g., "60cm x 80cm")
            category: Category of the artwork
            
        Returns:
            Description text
        """
        print(f"  → Generating description...")
        
        # Encode image
        image_data = self._encode_image(image_path)
        media_type = self._get_image_media_type(image_path)
        
        # Format prompt with metadata
        prompt = DESCRIPTION_GENERATION_PROMPT.format(
            title=title,
            medium=medium,
            dimensions=dimensions,
            category=category,
        )
        
        # Call Claude API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )
        
        # Return description text
        return message.content[0].text.strip()
    
    def get_image_dimensions(self, image_path: Path) -> str:
        """
        Extract dimensions from image EXIF data or actual pixel dimensions.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dimensions string (e.g., "60cm x 80cm" or "3000px x 2000px")
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Try to get DPI for physical dimensions
                dpi = img.info.get('dpi', (72, 72))
                if isinstance(dpi, tuple):
                    dpi = dpi[0]
                
                # Calculate physical dimensions in cm (if DPI is meaningful)
                if dpi and dpi > 0:
                    width_cm = round((width / dpi) * 2.54, 1)
                    height_cm = round((height / dpi) * 2.54, 1)
                    return f"{width_cm}cm x {height_cm}cm"
                else:
                    # Return pixel dimensions
                    return f"{width}px x {height}px"
        except Exception as e:
            print(f"  ⚠ Warning: Could not extract dimensions: {e}")
            return "Dimensions unknown"
