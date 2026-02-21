"""
Flickr platform integration.
Posts artwork to Flickr via the REST API using OAuth 1.0a.
Uses urllib.request (no external dependencies).
"""

import base64
import hashlib
import hmac
import json
import mimetypes
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from src.social.base import SocialPlatform, PostResult

UPLOAD_URL = "https://up.flickr.com/services/upload/"
REST_URL = "https://www.flickr.com/services/rest/"


class FlickrPlatform(SocialPlatform):
    """Flickr photo sharing platform integration."""

    name = "flickr"
    display_name = "Flickr"
    supports_video = False
    supports_images = True
    max_text_length = 63206  # Flickr description limit
    _is_stub = False

    def __init__(self):
        from config.settings import (
            FLICKR_API_KEY, FLICKR_API_SECRET,
            FLICKR_OAUTH_TOKEN, FLICKR_OAUTH_SECRET,
        )
        self.api_key = FLICKR_API_KEY
        self.api_secret = FLICKR_API_SECRET
        self.oauth_token = FLICKR_OAUTH_TOKEN
        self.oauth_token_secret = FLICKR_OAUTH_SECRET
        self._user_nsid: Optional[str] = None

    def is_configured(self) -> bool:
        return bool(
            self.api_key and self.api_secret
            and self.oauth_token and self.oauth_token_secret
        )

    def verify_credentials(self) -> bool:
        """Verify credentials via flickr.test.login. Caches user NSID on success."""
        if not self.is_configured():
            return False
        try:
            data = self._call_api({"method": "flickr.test.login", "format": "json", "nojsoncallback": "1"})
            if data.get("stat") == "ok":
                self._user_nsid = data.get("user", {}).get("id")
                return True
            return False
        except (HTTPError, URLError, Exception):
            return False

    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        """Upload a photo to Flickr. Uses alt_text as title, text as description."""
        if not self.is_configured():
            return PostResult(success=False, error="Flickr not configured")

        title = alt_text or image_path.stem.replace("_", " ").title()
        description = text

        try:
            photo_id = self._upload_photo(image_path, title, description)
            if not photo_id:
                return PostResult(success=False, error="Upload succeeded but no photo ID returned")

            url = self._photo_url(photo_id)
            return PostResult(success=True, post_url=url)

        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return PostResult(success=False, error=f"HTTP {e.code}: {body}")
        except URLError as e:
            return PostResult(success=False, error=f"Connection error: {e.reason}")
        except RuntimeError as e:
            return PostResult(success=False, error=str(e))
        except Exception as e:
            return PostResult(success=False, error=str(e))

    def post_video(self, video_path: Path, text: str) -> PostResult:
        raise NotImplementedError("Flickr video posting not yet implemented")

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _oauth_params(self) -> dict:
        """Return fresh base OAuth 1.0a parameters (no signature)."""
        return {
            "oauth_consumer_key": self.api_key,
            "oauth_nonce": uuid.uuid4().hex,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": self.oauth_token,
            "oauth_version": "1.0",
        }

    def _sign(self, method: str, url: str, params: dict) -> str:
        """Generate HMAC-SHA1 OAuth 1.0a signature over all params."""
        encoded = {
            quote(str(k), safe=""): quote(str(v), safe="")
            for k, v in params.items()
        }
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(encoded.items()))
        base_string = "&".join([
            method.upper(),
            quote(url, safe=""),
            quote(sorted_params, safe=""),
        ])
        signing_key = f"{quote(self.api_secret, safe='')}&{quote(self.oauth_token_secret, safe='')}"
        digest = hmac.new(
            signing_key.encode("utf-8"),
            base_string.encode("utf-8"),
            digestmod=hashlib.sha1,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _call_api(self, params: dict) -> dict:
        """Call a Flickr REST API method via GET. Returns parsed JSON dict."""
        oauth = self._oauth_params()
        all_params = {**oauth, **params}
        all_params["oauth_signature"] = self._sign("GET", REST_URL, all_params)
        url = f"{REST_URL}?{urlencode(all_params)}"
        with urlopen(Request(url), timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _upload_photo(self, image_path: Path, title: str, description: str) -> Optional[str]:
        """
        Upload a photo to Flickr. Returns the photo ID or None.

        For the upload endpoint, all OAuth params (including signature) go in
        the multipart form body — not the Authorization header.
        """
        content_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"

        # Build all params that will be signed (OAuth + upload metadata)
        oauth = self._oauth_params()
        upload_params = {
            "title": title,
            "description": description,
            "is_public": "1",
            "safety_level": "1",
            "content_type": "1",
        }
        all_params = {**oauth, **upload_params}
        all_params["oauth_signature"] = self._sign("POST", UPLOAD_URL, all_params)

        # Build multipart body
        boundary = uuid.uuid4().hex
        body = b""

        for key, value in all_params.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            body += str(value).encode("utf-8")
            body += b"\r\n"

        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="photo"; filename="{image_path.name}"\r\n'.encode()
        body += f"Content-Type: {content_type}\r\n\r\n".encode()
        body += image_path.read_bytes()
        body += b"\r\n"
        body += f"--{boundary}--\r\n".encode()

        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        req = Request(UPLOAD_URL, data=body, headers=headers, method="POST")
        with urlopen(req, timeout=120) as resp:
            xml_response = resp.read().decode("utf-8")

        root = ET.fromstring(xml_response)
        if root.get("stat") != "ok":
            err = root.find("err")
            msg = err.get("msg", "Unknown error") if err is not None else "Unknown error"
            raise RuntimeError(f"Flickr upload failed: {msg}")

        photo_id_el = root.find("photoid")
        return photo_id_el.text if photo_id_el is not None else None

    def _photo_url(self, photo_id: str) -> Optional[str]:
        """
        Build the canonical Flickr photo URL.
        If NSID not yet cached, fetches it via flickr.test.login.
        """
        if not self._user_nsid:
            try:
                data = self._call_api({
                    "method": "flickr.test.login",
                    "format": "json",
                    "nojsoncallback": "1",
                })
                self._user_nsid = data.get("user", {}).get("id", "")
            except Exception:
                return None

        if self._user_nsid:
            return f"https://www.flickr.com/photos/{self._user_nsid}/{photo_id}/"
        return None
