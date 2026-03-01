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
from src.core.logger import get_logger

logger = get_logger("metadata")


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
        Generate 10 diverse title options for an artwork.

        Args:
            image_path: Path to the artwork image

        Returns:
            List of 10 title strings
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
            if isinstance(titles, list) and len(titles) == 10:
                return titles
            else:
                raise ValueError("Response is not a list of 10 titles")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ⚠ Warning: Could not parse titles as JSON: {e}")
            print(f"  Raw response: {response_text}")
            logger.warning("Could not parse title response as JSON: %s", e)
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
        if len(matches) >= 10:
            return matches[:10]

        # If that fails, split by lines and take first 10 non-empty
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return lines[:10] if len(lines) >= 10 else lines + ["Untitled"] * (10 - len(lines))
    
    def generate_description(
        self,
        image_path: Path,
        title: str,
        medium: str,
        dimensions: str,
        category: str,
        user_notes: str = None,
    ) -> str:
        """
        Generate a gallery-quality description for an artwork.

        Args:
            image_path: Path to the artwork image
            title: Selected title for the artwork
            medium: Medium used (e.g., "Oil on canvas")
            dimensions: Dimensions string (e.g., "60cm x 80cm")
            category: Category of the artwork
            user_notes: Optional notes from the artist about the painting

        Returns:
            Description text
        """
        print(f"  → Generating description...")

        # Encode image
        image_data = self._encode_image(image_path)
        media_type = self._get_image_media_type(image_path)

        # Build user notes section if provided
        user_notes_section = ""
        if user_notes:
            user_notes_section = f"\nArtist's Notes: {user_notes}\n"

        # Format prompt with metadata
        prompt = DESCRIPTION_GENERATION_PROMPT.format(
            title=title,
            medium=medium,
            dimensions=dimensions,
            category=category,
            user_notes_section=user_notes_section,
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
    
    def generate_social_description(
        self,
        image_path: Path,
        title: str,
        max_chars: int = 200,
    ) -> str:
        """
        Generate a short description for social media posts.

        Args:
            image_path: Path to the artwork image
            title: Title of the artwork
            max_chars: Maximum characters for the description

        Returns:
            Short description text (max_chars or less)
        """
        print(f"  → Generating social media description...")

        # Encode image
        image_data = self._encode_image(image_path)
        media_type = self._get_image_media_type(image_path)

        # Create prompt for short description
        prompt = f"""You are writing a brief, engaging social media description for this artwork titled "{title}".

Write a concise description that:
- Captures the essence and mood of the painting in 1-2 sentences
- Is engaging and compelling for social media
- Is MAXIMUM {max_chars} characters (including spaces)
- Focuses on what makes this piece special or interesting
- Uses accessible, inviting language

Return ONLY the description text, nothing else. No hashtags, no title repetition, just the description."""

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

        # Get and truncate description if needed
        description = message.content[0].text.strip()
        if len(description) > max_chars:
            description = description[:max_chars - 3] + "..."

        return description

    def summarize_to_short_description(
        self,
        long_description: str,
        max_chars: int = 200,
    ) -> str:
        """
        Summarize a long gallery description to a short social media description.

        Args:
            long_description: The full gallery description text
            max_chars: Maximum characters for the short description

        Returns:
            Summarized short description (max_chars or less)
        """
        # Create prompt for summarization
        prompt = f"""Summarize this art gallery description into a brief, engaging social media post.

Original description:
{long_description}

Create a concise summary that:
- Captures the key essence and mood in 1-2 sentences
- Is MAXIMUM {max_chars} characters (including spaces)
- Is engaging for social media
- Focuses on what makes this piece special

Return ONLY the summary text, nothing else. No hashtags, no extra commentary."""

        # Call Claude API (text-only, no image needed)
        message = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # Get and truncate if needed
        short_desc = message.content[0].text.strip()
        if len(short_desc) > max_chars:
            short_desc = short_desc[:max_chars - 3] + "..."

        return short_desc

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
            logger.warning("Could not extract dimensions from %s: %s", image_path, e)
            return "Dimensions unknown"
