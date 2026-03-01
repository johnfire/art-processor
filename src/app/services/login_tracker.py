"""Tracks manual login timestamps for browser-session platforms.

Platforms that require periodic manual re-login (Cara, FASO) store their
last-login date here. Admin mode reads this to show renewal alerts.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

DEFAULT_MAX_DAYS = 30

# Platforms that require manual browser login
BROWSER_LOGIN_PLATFORMS = ["faso", "cara"]

# Warn when this many days remain before expiry
WARN_DAYS_REMAINING = 7


class LoginTracker:
    def __init__(self, status_path: Path):
        self.path = status_path
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {p: {"last_login": None, "max_days": DEFAULT_MAX_DAYS} for p in BROWSER_LOGIN_PLATFORMS}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2))

    def record_login(self, platform: str):
        """Record a successful manual login for a platform."""
        if platform not in self._data:
            self._data[platform] = {"last_login": None, "max_days": DEFAULT_MAX_DAYS}
        self._data[platform]["last_login"] = datetime.now().isoformat()
        self._save()

    def get_status(self, platform: str) -> dict:
        """Return login status dict for a platform.

        Status values: "never", "ok", "warn", "expired"
        """
        entry = self._data.get(platform, {"last_login": None, "max_days": DEFAULT_MAX_DAYS})
        last_login_str = entry.get("last_login")
        max_days = entry.get("max_days", DEFAULT_MAX_DAYS)

        if not last_login_str:
            return {
                "last_login": None,
                "days_since": None,
                "max_days": max_days,
                "days_remaining": None,
                "status": "never",
            }

        last_login = datetime.fromisoformat(last_login_str)
        days_since = (datetime.now() - last_login).days
        days_remaining = max_days - days_since

        if days_remaining <= 0:
            status = "expired"
        elif days_remaining <= WARN_DAYS_REMAINING:
            status = "warn"
        else:
            status = "ok"

        return {
            "last_login": last_login,
            "days_since": days_since,
            "max_days": max_days,
            "days_remaining": days_remaining,
            "status": status,
        }

    def get_alerts(self) -> list:
        """Return list of (platform, status_dict) for platforms needing attention."""
        alerts = []
        for platform in BROWSER_LOGIN_PLATFORMS:
            s = self.get_status(platform)
            if s["status"] in ("expired", "warn", "never"):
                alerts.append((platform, s))
        return alerts
