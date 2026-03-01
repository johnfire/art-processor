"""
Tumblr platform integration.
Posts artwork to Tumblr via the pytumblr OAuth 1.0a client.

Authentication uses four pre-generated keys stored in .env — no interactive
login flow is needed at runtime. To obtain them the first time:
  1. Register an app at https://www.tumblr.com/oauth/apps
  2. Use Tumblr's OAuth console at https://api.tumblr.com/console
     to generate TUMBLR_OAUTH_TOKEN and TUMBLR_OAUTH_SECRET.
"""

from pathlib import Path

from src.app.social.base import SocialPlatform, PostResult


class TumblrPlatform(SocialPlatform):
    """Tumblr social media platform integration via pytumblr."""

    name = "tumblr"
    display_name = "Tumblr"
    supports_video = False   # video upload not yet implemented
    supports_images = True
    max_text_length = 0      # Tumblr captions have no enforced length limit
    _is_stub = False

    def __init__(self):
        from config.settings import (
            TUMBLR_CONSUMER_KEY,
            TUMBLR_CONSUMER_SECRET,
            TUMBLR_OAUTH_TOKEN,
            TUMBLR_OAUTH_SECRET,
            TUMBLR_BLOG_NAME,
        )
        self.consumer_key = TUMBLR_CONSUMER_KEY
        self.consumer_secret = TUMBLR_CONSUMER_SECRET
        self.oauth_token = TUMBLR_OAUTH_TOKEN
        self.oauth_secret = TUMBLR_OAUTH_SECRET
        self.blog_name = TUMBLR_BLOG_NAME

    def is_configured(self) -> bool:
        """All five credentials must be present."""
        return bool(
            self.consumer_key
            and self.consumer_secret
            and self.oauth_token
            and self.oauth_secret
            and self.blog_name
        )

    def verify_credentials(self) -> bool:
        """Verify by fetching the authenticated user info."""
        if not self.is_configured():
            return False
        try:
            client = self._get_client()
            response = client.info()
            # pytumblr returns the response body directly (no meta wrapper):
            # success → {"user": {...}}, failure → {"errors": [...]}
            return "user" in response
        except Exception:
            return False

    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        """
        Post an image to Tumblr.

        The text argument is used as the caption body.
        If the metadata manager has set a title on the image, it is expected
        to already be prepended by the formatter — Tumblr captions support
        basic HTML so the caption is passed through as-is.

        Tags are not handled here; the formatter appends them to `text`
        for platforms that use inline hashtags.  Tumblr uses a separate
        tags list — pass them via a subclass or extend this method if needed.
        """
        if not self.is_configured():
            return PostResult(success=False, error="Tumblr not configured")

        try:
            from config.settings import TUMBLR_DEFAULT_STATE, TUMBLR_MAX_TAGS

            client = self._get_client()

            # Tumblr's create_photo accepts a local file path via 'data'
            response = client.create_photo(
                blogname=self.blog_name,
                state=TUMBLR_DEFAULT_STATE,
                caption=text,
                data=str(image_path),
            )

            # pytumblr returns the response body directly:
            # success → {"id": 12345, ...}, failure → {"errors": [...]}
            if "errors" in response:
                return PostResult(success=False, error=str(response["errors"]))
            if "id" not in response:
                return PostResult(success=False, error=f"Unexpected response: {response}")

            post_id = str(response["id"])
            post_url = f"https://{self.blog_name}.tumblr.com/post/{post_id}"

            return PostResult(success=True, post_url=post_url)

        except Exception as e:
            return PostResult(success=False, error=str(e))

    def post_image_with_tags(
        self,
        image_path: Path,
        text: str,
        tags: list,
        alt_text: str = "",
    ) -> PostResult:
        """
        Post an image with a separate tags list.

        Tumblr tags are a plain list of strings (no # prefix).
        Tags beyond TUMBLR_MAX_TAGS are silently dropped.
        """
        if not self.is_configured():
            return PostResult(success=False, error="Tumblr not configured")

        try:
            from config.settings import TUMBLR_DEFAULT_STATE, TUMBLR_MAX_TAGS

            client = self._get_client()
            safe_tags = tags[:TUMBLR_MAX_TAGS]

            response = client.create_photo(
                blogname=self.blog_name,
                state=TUMBLR_DEFAULT_STATE,
                caption=text,
                tags=safe_tags,
                data=str(image_path),
            )

            if "errors" in response:
                return PostResult(success=False, error=str(response["errors"]))
            if "id" not in response:
                return PostResult(success=False, error=f"Unexpected response: {response}")

            post_id = str(response["id"])
            post_url = f"https://{self.blog_name}.tumblr.com/post/{post_id}"

            return PostResult(success=True, post_url=post_url)

        except Exception as e:
            return PostResult(success=False, error=str(e))

    def post_video(self, video_path: Path, text: str) -> PostResult:
        """Video posting not yet implemented for Tumblr."""
        raise NotImplementedError("Tumblr video posting not yet implemented")

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _get_client(self):
        """Return an authenticated pytumblr client."""
        import pytumblr
        return pytumblr.TumblrRestClient(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            oauth_token=self.oauth_token,
            oauth_secret=self.oauth_secret,
        )
