"""
Bluesky platform integration.
Posts artwork to Bluesky via the AT Protocol API.
Uses the atproto SDK (synchronous client).
"""

import io
from pathlib import Path

from src.social.base import SocialPlatform, PostResult


class BlueskyPlatform(SocialPlatform):
    """Bluesky social media platform integration."""

    name = "bluesky"
    display_name = "Bluesky"
    supports_video = False   # Bluesky video upload requires async flow; not yet implemented
    supports_images = True
    max_text_length = 300
    _is_stub = False

    def __init__(self):
        from config.settings import BLUESKY_HANDLE, BLUESKY_APP_PASSWORD
        self.handle = BLUESKY_HANDLE
        self.app_password = BLUESKY_APP_PASSWORD
        self._client = None  # Lazy-initialised on first use; SDK handles token refresh

    def is_configured(self) -> bool:
        """Check if Bluesky handle and app password are present."""
        return bool(self.handle and self.app_password)

    def verify_credentials(self) -> bool:
        """Verify credentials by attempting login. Returns True if successful."""
        if not self.is_configured():
            return False
        try:
            self._get_client()
            return True
        except Exception as e:
            # Re-raise so the caller can show the real error message
            raise RuntimeError(f"Bluesky login failed: {e}") from e

    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        """
        Post an image with caption text to Bluesky.

        Flow:
        1. Enforce 300-character limit
        2. Strip EXIF from image (privacy + Bluesky recommendation)
        3. Upload image as blob, receive blob reference
        4. Create post with text + embedded image blob
        """
        if not self.is_configured():
            return PostResult(success=False, error="Bluesky not configured")

        # Bluesky enforces a hard 300-character limit
        if len(text) > self.max_text_length:
            return PostResult(
                success=False,
                error=f"Text exceeds {self.max_text_length} character limit ({len(text)} chars)"
            )

        try:
            from atproto import models

            client = self._get_client()

            # Strip EXIF metadata before uploading (recommended by Bluesky for privacy)
            img_data = self._strip_exif(image_path)

            # Upload image as a blob — returns a blob reference used in the embed
            upload_response = client.upload_blob(img_data)

            # Build the image embed with alt text for accessibility
            embed = models.AppBskyEmbedImages.Main(
                images=[
                    models.AppBskyEmbedImages.Image(
                        alt=alt_text,
                        image=upload_response.blob
                    )
                ]
            )

            # Create the post with text and embedded image
            post = client.send_post(text=text, embed=embed)

            return PostResult(success=True, post_url=post.uri)

        except Exception as e:
            return PostResult(success=False, error=str(e))

    def post_video(self, video_path: Path, text: str) -> PostResult:
        """Video posting not yet implemented for Bluesky."""
        raise NotImplementedError("Bluesky video posting not yet implemented")

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _get_client(self):
        """
        Return an authenticated AT Protocol client.
        Creates and logs in on first call; reuses the same instance afterwards
        so the SDK can handle token refresh automatically.
        """
        if self._client is None:
            from atproto import Client
            self._client = Client()
            self._client.login(self.handle, self.app_password)
        return self._client

    def _strip_exif(self, image_path: Path) -> bytes:
        """
        Strip EXIF metadata from an image before uploading.
        Re-encodes the image without EXIF data; format is preserved where possible.
        Returns raw image bytes.
        """
        from PIL import Image

        img = Image.open(image_path)
        buffer = io.BytesIO()
        img.save(buffer, format=img.format or "JPEG")
        return buffer.getvalue()
