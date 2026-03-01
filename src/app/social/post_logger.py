"""
Persistent logging for social media post attempts.

Writes structured log entries to LOGS_DIR/social.log so failures are
captured even when running headlessly (cron, scheduler).

Log format (one block per attempt):
  [2026-02-16 20:15:23] SUCCESS  platform=cara  painting='Zuiderwolde'
    image=/path/to/image.jpg  url=https://cara.app/...

  [2026-02-16 20:15:23] FAILURE  platform=bluesky  painting='The Canal'
    image=/path/to/image.jpg
    error: Text exceeds 300 character limit (312 chars)

  [2026-02-16 20:15:23] FAILURE  platform=cara  painting='The Beach'
    image=/path/to/image.jpg
    error: Timeout 30000ms exceeded waiting for locator("button[type='submit']")
    screenshots: cara_03_after_upload.png, cara_error.png
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Platforms that use Playwright — point to screenshots on failure
_PLAYWRIGHT_PLATFORMS = {"cara", "instagram"}


def _get_logger() -> logging.Logger:
    """Return (or create) the social-posts file logger.

    Lazy-initialised so the log file is only created when something is
    actually logged, and test runs that never call these functions don't
    create stray files.
    """
    from config.settings import LOGS_DIR

    logger = logging.getLogger("theo.social.posts")
    if not logger.handlers:
        from datetime import datetime
        log_file = LOGS_DIR / "social.log"
        handler = logging.FileHandler(log_file, encoding="utf-8")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        handler.stream.write(f"\n{'x' * 22} {now} {'x' * 22}\n")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # don't bubble up to the root logger
    return logger


def log_post_success(
    platform: str,
    title: str,
    image_path: Optional[Path],
    post_url: Optional[str],
) -> None:
    """Write a success entry to the social log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    img_part = f"  image={image_path}" if image_path else ""
    url_part = f"  url={post_url}" if post_url else ""
    _get_logger().info(
        f"[{timestamp}] SUCCESS  platform={platform}  painting={title!r}{img_part}{url_part}"
    )


def log_post_failure(
    platform: str,
    title: str,
    image_path: Optional[Path],
    error: str,
) -> None:
    """Write a failure entry with as much diagnostic context as possible.

    For Playwright-based platforms, also lists the most recent screenshots
    so you can open them to see exactly where the automation broke.
    """
    from config.settings import SCREENSHOTS_DIR

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    img_part = f"\n  image: {image_path}" if image_path else ""

    lines = [
        f"[{timestamp}] FAILURE  platform={platform}  painting={title!r}{img_part}",
        f"  error: {error}",
    ]

    # For Playwright platforms, surface the most recent screenshots
    if platform in _PLAYWRIGHT_PLATFORMS:
        screenshots = sorted(SCREENSHOTS_DIR.glob(f"{platform}_*.png"))
        if screenshots:
            # Show last 4 — covers the step-by-step numbered shots + error shot
            recent = screenshots[-4:]
            lines.append(
                "  screenshots: " + ", ".join(s.name for s in recent)
            )
            lines.append(f"  screenshot dir: {SCREENSHOTS_DIR}")

    _get_logger().error("\n".join(lines))


def log_credential_failure(platform: str) -> None:
    """Write an entry when credential verification fails at post time."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _get_logger().warning(
        f"[{timestamp}] CREDENTIAL FAILURE  platform={platform}  "
        f"credentials invalid or missing"
    )
