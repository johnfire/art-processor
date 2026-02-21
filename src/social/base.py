"""
Base classes for social media platform integrations.
Social media platforms are used for promotion and audience engagement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class PostResult:
    """Result of a social media post attempt."""
    success: bool
    post_url: Optional[str] = None
    error: Optional[str] = None


class SocialPlatform(ABC):
    """Abstract base class for social media platform integrations."""

    name: str = ""               # e.g. "mastodon"
    display_name: str = ""       # e.g. "Mastodon"
    supports_video: bool = False
    supports_images: bool = True
    max_text_length: int = 500

    @abstractmethod
    def verify_credentials(self) -> bool:
        """Verify that credentials are valid. Returns True if authenticated."""
        ...

    @abstractmethod
    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        """Post an image with text to the platform."""
        ...

    @abstractmethod
    def post_video(self, video_path: Path, text: str) -> PostResult:
        """Post a video with text to the platform."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if required credentials/config are present."""
        ...


def default_social_media_entry() -> dict:
    """Return the default tracking entry for a social media platform."""
    return {"last_posted": None, "post_url": None, "post_count": 0}


# All social media platform names tracked in metadata
SOCIAL_MEDIA_PLATFORMS = [
    "mastodon",
    "instagram",
    "facebook",
    "bluesky",
    "linkedin",
    "tiktok",
    "youtube",
    "cara",
    "threads",
    "pixelfed",
    "flickr",
    "upscrolled",
]


def empty_social_media_dict() -> dict:
    """Return a social_media dict with all platforms initialized to defaults."""
    return {name: default_social_media_entry() for name in SOCIAL_MEDIA_PLATFORMS}
