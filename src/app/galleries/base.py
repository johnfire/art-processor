"""
Base classes for art gallery website integrations.
Gallery platforms are portfolio/sales sites where artwork is displayed and sold.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class UploadResult:
    """Result of a gallery upload attempt."""
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None


class GalleryPlatform(ABC):
    """Abstract base class for art gallery website integrations."""

    name: str = ""               # e.g. "faso"
    display_name: str = ""       # e.g. "FASO"
    requires_browser: bool = False

    @abstractmethod
    def upload_artwork(self, metadata: Dict[str, Any]) -> UploadResult:
        """Upload artwork with metadata to the gallery site."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if required credentials/config are present."""
        ...


def default_gallery_entry() -> dict:
    """Return the default tracking entry for a gallery site."""
    return {"last_uploaded": None, "url": None}


# All gallery platform names tracked in metadata
GALLERY_PLATFORMS = [
    "faso",
]


def empty_gallery_sites_dict() -> dict:
    """Return a gallery_sites dict with all platforms initialized to defaults."""
    return {name: default_gallery_entry() for name in GALLERY_PLATFORMS}
