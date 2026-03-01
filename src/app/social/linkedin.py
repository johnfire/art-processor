"""LinkedIn platform integration (not yet implemented)."""

from pathlib import Path
from src.app.social.base import SocialPlatform, PostResult


class LinkedInPlatform(SocialPlatform):
    name = "linkedin"
    display_name = "LinkedIn"
    supports_video = True
    supports_images = True
    max_text_length = 3000
    _is_stub = True

    def verify_credentials(self) -> bool:
        raise NotImplementedError("LinkedIn integration not yet implemented")

    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        raise NotImplementedError("LinkedIn integration not yet implemented")

    def post_video(self, video_path: Path, text: str) -> PostResult:
        raise NotImplementedError("LinkedIn integration not yet implemented")

    def is_configured(self) -> bool:
        return False
