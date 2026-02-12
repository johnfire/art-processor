"""
Social media post scheduler.
Manages scheduled posts and executes them when due.
Designed to be called by a cron job every 5 minutes.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class Scheduler:
    """Manages scheduled social media posts."""

    def __init__(self, schedule_file: Path = None):
        if schedule_file is None:
            from config.settings import SCHEDULE_PATH
            schedule_file = SCHEDULE_PATH
        self.schedule_file = schedule_file
        self.data = self._load()

    def _load(self) -> Dict:
        """Load schedule data from file."""
        if self.schedule_file.exists():
            with open(self.schedule_file, "r") as f:
                return json.load(f)
        return {"scheduled_posts": []}

    def _save(self):
        """Save schedule data to file."""
        with open(self.schedule_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_post(
        self,
        content_id: str,
        metadata_path: str,
        platform: str,
        scheduled_time: str,
        content_type: str = "painting",
    ) -> str:
        """
        Schedule a new post.

        Args:
            content_id: Painting/video filename base.
            metadata_path: Path to the metadata JSON file.
            platform: Social media platform name.
            scheduled_time: ISO format datetime string.
            content_type: "painting" or "video".

        Returns:
            The ID of the scheduled post.
        """
        post_id = uuid.uuid4().hex[:8]
        entry = {
            "id": post_id,
            "content_type": content_type,
            "content_id": content_id,
            "metadata_path": metadata_path,
            "platform": platform,
            "scheduled_time": scheduled_time,
            "status": "pending",
            "post_url": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
        }
        self.data["scheduled_posts"].append(entry)
        self._save()
        return post_id

    def get_pending(self) -> List[Dict]:
        """Get posts that are due now (pending and scheduled_time <= now)."""
        now = datetime.now().isoformat()
        return [
            p for p in self.data["scheduled_posts"]
            if p["status"] == "pending" and p["scheduled_time"] <= now
        ]

    def get_upcoming(self) -> List[Dict]:
        """Get all future pending posts (not yet due)."""
        now = datetime.now().isoformat()
        return [
            p for p in self.data["scheduled_posts"]
            if p["status"] == "pending" and p["scheduled_time"] > now
        ]

    def cancel_post(self, post_id: str) -> bool:
        """Cancel a scheduled post. Returns True if found and cancelled."""
        for post in self.data["scheduled_posts"]:
            if post["id"] == post_id and post["status"] == "pending":
                post["status"] = "cancelled"
                self._save()
                return True
        return False

    def mark_posted(self, post_id: str, post_url: Optional[str] = None):
        """Mark a scheduled post as successfully posted."""
        for post in self.data["scheduled_posts"]:
            if post["id"] == post_id:
                post["status"] = "posted"
                post["post_url"] = post_url
                self._save()
                return

    def mark_failed(self, post_id: str, error: str):
        """Mark a scheduled post as failed."""
        for post in self.data["scheduled_posts"]:
            if post["id"] == post_id:
                post["status"] = "failed"
                post["error"] = error
                self._save()
                return

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get completed and failed posts, most recent first."""
        done = [
            p for p in self.data["scheduled_posts"]
            if p["status"] in ("posted", "failed")
        ]
        done.sort(key=lambda p: p.get("scheduled_time", ""), reverse=True)
        return done[:limit]

    def execute_pending(self) -> Dict[str, int]:
        """
        Execute all posts that are due now.
        Updates metadata JSONs with post_count and last_posted.

        Returns:
            Dict with counts: {"posted": N, "failed": N, "skipped": N}
        """
        from src.social import get_platform
        from src.social.formatter import format_post_text

        pending = self.get_pending()
        results = {"posted": 0, "failed": 0, "skipped": 0}

        for post in pending:
            platform_name = post["platform"]
            metadata_path = Path(post["metadata_path"])

            # Load metadata
            if not metadata_path.exists():
                self.mark_failed(post["id"], f"Metadata not found: {metadata_path}")
                results["failed"] += 1
                continue

            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            # Get platform
            try:
                platform = get_platform(platform_name)
            except KeyError:
                self.mark_failed(post["id"], f"Unknown platform: {platform_name}")
                results["failed"] += 1
                continue

            if not platform.is_configured():
                self.mark_failed(post["id"], f"{platform.display_name} not configured")
                results["failed"] += 1
                continue

            # Build post text
            text = format_post_text(metadata, max_words=75)

            # Get image path
            image_path = _get_image_path(metadata)
            if not image_path or not image_path.exists():
                self.mark_failed(post["id"], "Image file not found")
                results["failed"] += 1
                continue

            # Post
            alt_text = metadata.get("description") or ""
            result = platform.post_image(image_path, text, alt_text)

            if result.success:
                self.mark_posted(post["id"], result.post_url)
                _update_social_media_tracking(metadata_path, metadata, platform_name, result.post_url)
                results["posted"] += 1
            else:
                self.mark_failed(post["id"], result.error or "Unknown error")
                results["failed"] += 1

        return results


def _get_image_path(metadata: dict) -> Optional[Path]:
    """Get the best image path from metadata (prefer instagram, skip big files for social media)."""
    from config.settings import PAINTINGS_INSTAGRAM_PATH

    files = metadata.get("files", {})
    filename_base = metadata.get("filename_base", "")
    # Use collection_folder if available, otherwise fall back to category
    collection_folder = metadata.get("collection_folder") or metadata.get("category", "")

    # Try instagram first (smaller, optimized for social)
    instagram = files.get("instagram")
    if instagram:
        if isinstance(instagram, list):
            for p in instagram:
                path = Path(p)
                if path.exists():
                    return path
        elif isinstance(instagram, str):
            path = Path(instagram)
            if path.exists():
                return path

    # Get actual filename from big file path (handles case mismatches)
    actual_filename = None
    big = files.get("big")
    if big:
        if isinstance(big, list) and big:
            actual_filename = Path(big[0]).name
        elif isinstance(big, str):
            actual_filename = Path(big).name

    # Construct instagram path using actual filename
    if actual_filename and collection_folder:
        constructed_instagram = PAINTINGS_INSTAGRAM_PATH / collection_folder / actual_filename
        if constructed_instagram.exists():
            return constructed_instagram

    # Try with filename_base as fallback
    if filename_base and collection_folder:
        constructed_instagram = PAINTINGS_INSTAGRAM_PATH / collection_folder / f"{filename_base}.jpg"
        if constructed_instagram.exists():
            return constructed_instagram

    # ONLY use instagram versions for social media (skip big files)
    return None


def _update_social_media_tracking(
    metadata_path: Path, metadata: dict, platform_name: str, post_url: Optional[str]
):
    """Update the social_media tracking in a metadata JSON file."""
    if "social_media" not in metadata:
        from src.social.base import empty_social_media_dict
        metadata["social_media"] = empty_social_media_dict()

    if platform_name not in metadata["social_media"]:
        from src.social.base import default_social_media_entry
        metadata["social_media"][platform_name] = default_social_media_entry()

    entry = metadata["social_media"][platform_name]
    entry["last_posted"] = datetime.now().isoformat()
    entry["post_url"] = post_url
    entry["post_count"] = entry.get("post_count", 0) + 1

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
