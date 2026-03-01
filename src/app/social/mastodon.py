"""
Mastodon platform integration.
Posts artwork to a Mastodon instance via the REST API.
Uses urllib.request (no external dependencies).
"""

import json
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from src.app.social.base import SocialPlatform, PostResult


class MastodonPlatform(SocialPlatform):
    """Mastodon social media platform integration."""

    name = "mastodon"
    display_name = "Mastodon"
    supports_video = True
    supports_images = True
    max_text_length = 500
    _is_stub = False

    def __init__(self):
        from config.settings import MASTODON_INSTANCE_URL, MASTODON_ACCESS_TOKEN
        self.instance_url = MASTODON_INSTANCE_URL.rstrip("/") if MASTODON_INSTANCE_URL else ""
        self.access_token = MASTODON_ACCESS_TOKEN

    def is_configured(self) -> bool:
        """Check if Mastodon instance URL and access token are set."""
        return bool(self.instance_url and self.access_token)

    def verify_credentials(self) -> bool:
        """Verify the access token is valid by checking the account endpoint."""
        if not self.is_configured():
            return False
        try:
            url = f"{self.instance_url}/api/v1/accounts/verify_credentials"
            req = Request(url, headers=self._auth_headers())
            with urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except (HTTPError, URLError):
            return False

    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        """Upload an image and create a status with it."""
        if not self.is_configured():
            return PostResult(success=False, error="Mastodon not configured")

        try:
            # Step 1: Upload media
            media_id = self._upload_media(image_path, alt_text)
            if not media_id:
                return PostResult(success=False, error="Failed to upload media")

            # Step 2: Create status with media
            return self._create_status(text, media_ids=[media_id])

        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return PostResult(success=False, error=f"HTTP {e.code}: {body}")
        except URLError as e:
            return PostResult(success=False, error=f"Connection error: {e.reason}")
        except Exception as e:
            return PostResult(success=False, error=str(e))

    def post_video(self, video_path: Path, text: str) -> PostResult:
        """Upload a video and create a status with it."""
        if not self.is_configured():
            return PostResult(success=False, error="Mastodon not configured")

        try:
            media_id = self._upload_media(video_path, "")
            if not media_id:
                return PostResult(success=False, error="Failed to upload video")

            return self._create_status(text, media_ids=[media_id])

        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return PostResult(success=False, error=f"HTTP {e.code}: {body}")
        except URLError as e:
            return PostResult(success=False, error=f"Connection error: {e.reason}")
        except Exception as e:
            return PostResult(success=False, error=str(e))

    def _auth_headers(self) -> dict:
        """Return authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def _upload_media(self, file_path: Path, description: str = "") -> Optional[str]:
        """
        Upload a media file to Mastodon.
        Returns the media ID or None on failure.
        """
        url = f"{self.instance_url}/api/v2/media"

        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        boundary = uuid.uuid4().hex

        # Build multipart form data
        body = b""

        # File field
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode()
        body += f"Content-Type: {content_type}\r\n\r\n".encode()
        body += file_path.read_bytes()
        body += b"\r\n"

        # Description field (alt text)
        if description:
            body += f"--{boundary}\r\n".encode()
            body += b'Content-Disposition: form-data; name="description"\r\n\r\n'
            body += description.encode("utf-8")
            body += b"\r\n"

        body += f"--{boundary}--\r\n".encode()

        headers = self._auth_headers()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

        req = Request(url, data=body, headers=headers, method="POST")
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("id")

    def _create_status(self, text: str, media_ids: list = None) -> PostResult:
        """Create a status (toot) on Mastodon."""
        url = f"{self.instance_url}/api/v1/statuses"

        payload = {"status": text}
        if media_ids:
            payload["media_ids"] = media_ids

        body = json.dumps(payload).encode("utf-8")

        headers = self._auth_headers()
        headers["Content-Type"] = "application/json"

        req = Request(url, data=body, headers=headers, method="POST")
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            post_url = data.get("url") or data.get("uri")
            return PostResult(success=True, post_url=post_url)
