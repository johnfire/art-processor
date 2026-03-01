"""TikTok platform integration (not yet implemented)."""

from pathlib import Path
from src.app.social.base import SocialPlatform, PostResult


class TikTokPlatform(SocialPlatform):
    name = "tiktok"
    display_name = "TikTok"
    supports_video = True
    supports_images = True
    max_text_length = 2200
    _is_stub = True

    def verify_credentials(self) -> bool:
        raise NotImplementedError("TikTok integration not yet implemented")

    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        raise NotImplementedError("TikTok integration not yet implemented")

    def post_video(self, video_path: Path, text: str) -> PostResult:
        raise NotImplementedError("TikTok integration not yet implemented")

    def is_configured(self) -> bool:
        return False
