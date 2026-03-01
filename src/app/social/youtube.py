"""YouTube platform integration (not yet implemented)."""

from pathlib import Path
from src.app.social.base import SocialPlatform, PostResult


class YouTubePlatform(SocialPlatform):
    name = "youtube"
    display_name = "YouTube"
    supports_video = True
    supports_images = False
    max_text_length = 5000
    _is_stub = True

    def verify_credentials(self) -> bool:
        raise NotImplementedError("YouTube integration not yet implemented")

    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        raise NotImplementedError("YouTube integration not yet implemented")

    def post_video(self, video_path: Path, text: str) -> PostResult:
        raise NotImplementedError("YouTube integration not yet implemented")

    def is_configured(self) -> bool:
        return False
