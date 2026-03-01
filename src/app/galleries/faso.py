"""
FASO gallery platform wrapper.
Wraps the existing faso_uploader.py to fit the GalleryPlatform interface.
"""

from typing import Dict, Any

from src.app.galleries.base import GalleryPlatform, UploadResult


class FASOGallery(GalleryPlatform):
    """FASO (Fine Art Studio Online) gallery integration."""

    name = "faso"
    display_name = "FASO"
    requires_browser = True

    def upload_artwork(self, metadata: Dict[str, Any]) -> UploadResult:
        """Upload artwork to FASO via the browser-based uploader."""
        # FASO uses browser automation, so the upload is handled
        # through the interactive upload_faso_cli() flow.
        # This wrapper exists for the gallery registry.
        raise NotImplementedError(
            "FASO uploads use browser automation. "
            "Use admin option 11 or 'python main.py upload-faso' instead."
        )

    def is_configured(self) -> bool:
        """Check if FASO credentials are configured."""
        from config.settings import FASO_EMAIL, FASO_PASSWORD
        return bool(FASO_EMAIL and FASO_EMAIL != "xxx" and FASO_PASSWORD and FASO_PASSWORD != "xxx")
