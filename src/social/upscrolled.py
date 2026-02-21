"""UpScrolled platform integration (not yet implemented).

UpScrolled has no public API as of 2026-02-21. Check back around 2026-04-22:
https://support.upscrolled.com/hc/en-us/articles/13581266207887-Do-you-provide-API-access
"""

from pathlib import Path
from src.social.base import SocialPlatform, PostResult


class UpScrolledPlatform(SocialPlatform):
    name = "upscrolled"
    display_name = "UpScrolled"
    supports_video = True
    supports_images = True
    max_text_length = 2200
    _is_stub = True

    def verify_credentials(self) -> bool:
        raise NotImplementedError("UpScrolled integration not yet implemented — no public API")

    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        raise NotImplementedError("UpScrolled integration not yet implemented — no public API")

    def post_video(self, video_path: Path, text: str) -> PostResult:
        raise NotImplementedError("UpScrolled integration not yet implemented — no public API")

    def is_configured(self) -> bool:
        return False
