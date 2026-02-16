"""
Pixelfed platform integration.
Posts artwork to a Pixelfed instance via the Mastodon-compatible API.

Pixelfed implements the Mastodon v1 API, so the pattern is identical to
the Mastodon integration — different env vars and v1/media instead of v2/media.
Uses urllib.request (no external HTTP dependencies).
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

from src.social.base import SocialPlatform, PostResult


class PixelfedPlatform(SocialPlatform):
    """Pixelfed social media platform integration."""

    name = "pixelfed"
    display_name = "Pixelfed"
    supports_video = False   # Pixelfed is image-first; video support varies by instance
    supports_images = True
    max_text_length = 2000   # safe default; varies by instance
    _is_stub = False

    def __init__(self):
        from config.settings import PIXELFED_INSTANCE_URL, PIXELFED_ACCESS_TOKEN
        self.instance_url = PIXELFED_INSTANCE_URL.rstrip("/") if PIXELFED_INSTANCE_URL else ""
        self.access_token = PIXELFED_ACCESS_TOKEN

    def is_configured(self) -> bool:
        """Check if Pixelfed instance URL and access token are set."""
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
        """
        Upload an image and create a post with it.

        Flow:
        1. Upload image via v1/media (Pixelfed does not support v2/media)
        2. Create status with the returned media ID attached
        """
        if not self.is_configured():
            return PostResult(success=False, error="Pixelfed not configured")

        try:
            # Step 1: Upload media using v1 endpoint (v2 returns 404 on Pixelfed)
            media_id = self._upload_media(image_path, alt_text)
            if not media_id:
                return PostResult(success=False, error="Failed to upload media")

            # Step 2: Create status — image attachment is mandatory on Pixelfed
            return self._create_status(text, media_ids=[media_id])

        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return PostResult(success=False, error=f"HTTP {e.code}: {body}")
        except URLError as e:
            return PostResult(success=False, error=f"Connection error: {e.reason}")
        except Exception as e:
            return PostResult(success=False, error=str(e))

    def post_video(self, video_path: Path, text: str) -> PostResult:
        """Video posting not yet implemented for Pixelfed."""
        raise NotImplementedError("Pixelfed video posting not yet implemented")

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _auth_headers(self) -> dict:
        """Return authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def _upload_media(self, file_path: Path, description: str = "") -> Optional[str]:
        """
        Upload a media file to Pixelfed.
        Uses api/v1/media — Pixelfed does not support the v2 endpoint.
        Returns the media ID or None on failure.
        """
        # Some Pixelfed instances don't honour the Bearer header on POST —
        # pass the token as a query param as well (belt-and-braces).
        url = f"{self.instance_url}/api/v1/media?access_token={self.access_token}"

        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        boundary = uuid.uuid4().hex

        # Build multipart form data manually (no external library)
        body = b""

        # File field
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode()
        body += f"Content-Type: {content_type}\r\n\r\n".encode()
        body += file_path.read_bytes()
        body += b"\r\n"

        # Description field (alt text for accessibility)
        if description:
            body += f"--{boundary}\r\n".encode()
            body += b'Content-Disposition: form-data; name="description"\r\n\r\n'
            body += description.encode("utf-8")
            body += b"\r\n"

        body += f"--{boundary}--\r\n".encode()

        headers = self._auth_headers()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        headers["Accept"] = "application/json"

        req = Request(url, data=body, headers=headers, method="POST")
        with urlopen(req, timeout=120) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
        if not raw.strip():
            raise ValueError(f"Empty response from {url} (HTTP {status})")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"HTTP {status} — Non-JSON response from {url}: {raw[:300]}")
        return data.get("id")

    def _create_status(self, text: str, media_ids: list = None) -> PostResult:
        """
        Create a status (post) on Pixelfed.
        Pixelfed requires at least one media attachment — never call without media_ids.
        """
        url = f"{self.instance_url}/api/v1/statuses?access_token={self.access_token}"

        payload = {"status": text, "visibility": "public"}
        if media_ids:
            payload["media_ids"] = media_ids

        body = json.dumps(payload).encode("utf-8")

        headers = self._auth_headers()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        req = Request(url, data=body, headers=headers, method="POST")
        with urlopen(req, timeout=30) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
        if not raw.strip():
            raise ValueError(f"Empty response from {url} (HTTP {status})")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"HTTP {status} — Non-JSON response from {url}: {raw[:300]}")
        post_url = data.get("url") or data.get("uri")
        return PostResult(success=True, post_url=post_url)
