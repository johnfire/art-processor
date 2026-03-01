"""
Migration script: moves upload tracking from upload_status.json into
each painting's metadata JSON as gallery_sites + social_media fields.

Run once: python -m src.migrate_tracking
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from rich.console import Console

from src.app.social.base import empty_social_media_dict
from src.app.galleries.base import empty_gallery_sites_dict

console = Console()


def migrate(tracker_path: Path = None, dry_run: bool = False):
    """
    Migrate upload_status.json data into individual metadata JSON files.

    Args:
        tracker_path: Path to upload_status.json. If None, uses settings.
        dry_run: If True, print what would happen without writing files.
    """
    if tracker_path is None:
        from config.settings import UPLOAD_TRACKER_PATH
        tracker_path = UPLOAD_TRACKER_PATH

    if not tracker_path.exists():
        console.print("[yellow]No upload_status.json found — nothing to migrate.[/yellow]")
        return

    with open(tracker_path, "r") as f:
        tracker_data = json.load(f)

    paintings = tracker_data.get("paintings", {})
    migrated = 0
    skipped = 0
    errors = 0

    for filename, info in paintings.items():
        metadata_path = Path(info.get("metadata_path", ""))

        if not metadata_path.exists():
            console.print(f"[yellow]Skipping {filename}: metadata not found at {metadata_path}[/yellow]")
            skipped += 1
            continue

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            # Add gallery_sites if missing
            if "gallery_sites" not in metadata:
                metadata["gallery_sites"] = empty_gallery_sites_dict()

            # Set FASO status from tracker
            faso_uploaded = info.get("uploads", {}).get("FASO", False)
            if faso_uploaded:
                metadata["gallery_sites"]["faso"]["last_uploaded"] = (
                    info.get("processed_date") or datetime.now().isoformat()
                )

            # Add social_media if missing
            if "social_media" not in metadata:
                metadata["social_media"] = empty_social_media_dict()

            if dry_run:
                console.print(f"[dim]Would update: {metadata_path}[/dim]")
                console.print(f"  FASO uploaded: {faso_uploaded}")
            else:
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                console.print(f"[green]Migrated: {filename}[/green]")

            migrated += 1

        except Exception as e:
            console.print(f"[red]Error migrating {filename}: {e}[/red]")
            errors += 1

    # Archive upload_status.json
    if not dry_run and migrated > 0:
        backup_path = tracker_path.with_suffix(".json.bak")
        shutil.copy2(tracker_path, backup_path)
        console.print(f"\n[dim]Archived {tracker_path.name} -> {backup_path.name}[/dim]")

    console.print(f"\n[bold]Migration complete:[/bold] {migrated} migrated, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    migrate()
