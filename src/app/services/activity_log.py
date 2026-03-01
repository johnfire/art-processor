"""
Activity logging for audit trail of admin and CLI actions.
Logs to ~/.config/theo-van-gogh/activity_log.txt

Each line format:
    [YYYY-MM-DD HH:MM:SS] [user|cron] <action description>
"""

import sys
from datetime import datetime
from pathlib import Path

_LOG_FILE = Path("~/.config/theo-van-gogh/activity_log.txt").expanduser()

_ADMIN_ACTION_NAMES = {
    1: "Edit Anthropic API Key",
    2: "Edit File Paths",
    3: "Edit Dimension Unit",
    4: "Add to Lists",
    5: "Manage Social Media Platforms",
    6: "Sync Collection Folders",
    7: "View Current Settings",
    8: "Generate Skeleton Metadata",
    9: "Edit Metadata",
    10: "Sync Instagram Folders",
    11: "Upload to FASO",
    12: "Find Painting",
    13: "Post to Social Media",
    14: "Schedule Posts",
    15: "View Schedule",
    16: "Migrate Tracking Data",
}


def get_source() -> str:
    """Return 'user' if running interactively, 'cron' if no TTY is attached."""
    return "user" if sys.stdin.isatty() else "cron"


def log_activity(action: str) -> None:
    """Append a timestamped activity entry to the activity log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = get_source()
    line = f"[{timestamp}] [{source}] {action}\n"
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOG_FILE, "a") as f:
        f.write(line)


def log_admin_action(choice: int) -> None:
    """Log an admin menu selection by its numeric choice."""
    name = _ADMIN_ACTION_NAMES.get(choice, f"Option {choice}")
    log_activity(f"Admin menu: {name}")
