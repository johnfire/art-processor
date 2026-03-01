"""
Instagram folder sync module.
Reorganizes my-paintings-instagram to match the subfolder structure of my-paintings-big.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from config.settings import (
    PAINTINGS_BIG_PATH,
    PAINTINGS_INSTAGRAM_PATH,
    SUPPORTED_IMAGE_FORMATS,
)

console = Console()


class InstagramFolderSync:
    """Syncs instagram folder structure to match big paintings structure."""

    def __init__(
        self,
        big_path: Path = PAINTINGS_BIG_PATH,
        instagram_path: Path = PAINTINGS_INSTAGRAM_PATH,
    ):
        self.big_path = big_path
        self.instagram_path = instagram_path

    def _is_image(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_FORMATS

    def flatten_instagram(self) -> Tuple[int, List[str]]:
        """
        Move all image files from instagram subfolders into the instagram root.
        Deletes empty subfolders afterward.

        Returns:
            Tuple of (files_moved, warnings)
        """
        moved = 0
        warnings = []

        if not self.instagram_path.exists():
            return 0, [f"Instagram path does not exist: {self.instagram_path}"]

        # Collect existing root filenames (case-insensitive) to detect collisions
        root_names = {}
        for f in self.instagram_path.iterdir():
            if self._is_image(f):
                root_names[f.name.lower()] = f

        # Move files from subfolders to root
        for subfolder in sorted(self.instagram_path.iterdir()):
            if not subfolder.is_dir() or subfolder.name.startswith("."):
                continue

            for file_path in sorted(subfolder.iterdir()):
                if not self._is_image(file_path):
                    continue

                target = self.instagram_path / file_path.name

                if target.exists() and target != file_path:
                    # Collision: rename with suffix
                    stem = file_path.stem
                    suffix = file_path.suffix
                    counter = 1
                    while target.exists():
                        target = self.instagram_path / f"{stem}_{counter}{suffix}"
                        counter += 1
                    warnings.append(
                        f"Renamed {file_path.name} -> {target.name} (collision)"
                    )

                shutil.move(str(file_path), str(target))
                moved += 1

        # Delete empty subfolders
        for subfolder in sorted(self.instagram_path.iterdir()):
            if not subfolder.is_dir() or subfolder.name.startswith("."):
                continue
            # Only delete if truly empty (no files, no subdirs with content)
            remaining = list(subfolder.iterdir())
            if not remaining:
                subfolder.rmdir()

        return moved, warnings

    def ensure_subfolders(self) -> List[str]:
        """
        Create subfolders in instagram that exist in big.

        Returns:
            List of created folder names
        """
        created = []

        if not self.big_path.exists():
            return created

        for subfolder in sorted(self.big_path.iterdir()):
            if not subfolder.is_dir() or subfolder.name.startswith("."):
                continue

            target = self.instagram_path / subfolder.name
            if not target.exists():
                target.mkdir(parents=True, exist_ok=True)
                created.append(subfolder.name)

        return created

    def match_and_move(self) -> Dict:
        """
        For each file in each big subfolder, look for a matching filename
        in the instagram root and move it into the corresponding subfolder.

        Returns:
            Dict with results per folder + overall stats
        """
        # Index all files currently in instagram root
        root_files = {}
        for f in self.instagram_path.iterdir():
            if self._is_image(f):
                root_files[f.name.lower()] = f

        folder_results = []
        total_matched = 0
        total_unmatched = 0
        unmatched_big = []

        for subfolder in sorted(self.big_path.iterdir()):
            if not subfolder.is_dir() or subfolder.name.startswith("."):
                continue

            matched = 0
            unmatched = 0

            for big_file in sorted(subfolder.iterdir()):
                if not self._is_image(big_file):
                    continue

                key = big_file.name.lower()
                if key in root_files:
                    # Move instagram file into matching subfolder
                    dest_folder = self.instagram_path / subfolder.name
                    dest_folder.mkdir(parents=True, exist_ok=True)
                    dest = dest_folder / root_files[key].name
                    shutil.move(str(root_files[key]), str(dest))
                    del root_files[key]
                    matched += 1
                else:
                    # Also check if already in the correct subfolder
                    existing = self.instagram_path / subfolder.name / big_file.name
                    if existing.exists():
                        matched += 1
                    else:
                        unmatched += 1
                        unmatched_big.append(f"{subfolder.name}/{big_file.name}")

            if matched > 0 or unmatched > 0:
                folder_results.append({
                    "folder": subfolder.name,
                    "matched": matched,
                    "unmatched": unmatched,
                })

            total_matched += matched
            total_unmatched += unmatched

        # Leftover files still in instagram root (no big counterpart)
        leftover = [f.name for f in sorted(root_files.values())]

        return {
            "folders": folder_results,
            "total_matched": total_matched,
            "total_unmatched": total_unmatched,
            "unmatched_big": unmatched_big,
            "leftover_instagram": leftover,
        }

    def sync(self) -> Dict:
        """
        Full sync: flatten → ensure subfolders → match & move.

        Returns:
            Complete results summary
        """
        # Step 1: Flatten
        flatten_moved, flatten_warnings = self.flatten_instagram()

        # Step 2: Ensure subfolders
        created_folders = self.ensure_subfolders()

        # Step 3: Match and move
        match_results = self.match_and_move()

        return {
            "flatten_moved": flatten_moved,
            "flatten_warnings": flatten_warnings,
            "created_folders": created_folders,
            **match_results,
        }


def sync_instagram_folders_cli() -> Dict:
    """CLI entry point for instagram folder sync. Called from admin mode."""
    syncer = InstagramFolderSync()

    console.print("\n[bold cyan]Instagram Folder Sync[/bold cyan]\n")
    console.print(f"Source (big):      {syncer.big_path}")
    console.print(f"Target (instagram): {syncer.instagram_path}\n")
    console.print(
        "[yellow]This will flatten all instagram files to the root, "
        "then reorganize them to match the big folder structure.[/yellow]\n"
    )

    if not Confirm.ask("Proceed?", default=False):
        return {}

    result = syncer.sync()

    # Flatten summary
    console.print(f"\n[bold]Step 1 - Flatten:[/bold] {result['flatten_moved']} files moved to root")
    if result["flatten_warnings"]:
        for w in result["flatten_warnings"]:
            console.print(f"  [yellow]* {w}[/yellow]")

    # Created folders
    if result["created_folders"]:
        console.print(f"\n[bold]Step 2 - Created folders:[/bold] {len(result['created_folders'])}")
        for f in result["created_folders"]:
            console.print(f"  [green]+ {f}[/green]")

    # Match results table
    if result["folders"]:
        console.print(f"\n[bold]Step 3 - Match & Move:[/bold]")
        table = Table(title="Results by Folder")
        table.add_column("Folder", style="cyan")
        table.add_column("Matched", justify="right", style="green")
        table.add_column("No Match", justify="right", style="yellow")

        for fr in result["folders"]:
            table.add_row(
                fr["folder"], str(fr["matched"]), str(fr["unmatched"])
            )

        console.print(table)

    console.print(f"\n[bold]Total matched:[/bold] [green]{result['total_matched']}[/green]")
    console.print(f"[bold]Total unmatched (big):[/bold] [yellow]{result['total_unmatched']}[/yellow]")

    # Warnings for unmatched big files
    if result["unmatched_big"]:
        console.print(f"\n[yellow]Big files with no instagram match ({len(result['unmatched_big'])}):[/yellow]")
        for f in result["unmatched_big"][:20]:
            console.print(f"  [dim]{f}[/dim]")
        if len(result["unmatched_big"]) > 20:
            console.print(f"  [dim]...and {len(result['unmatched_big']) - 20} more[/dim]")

    # Leftover instagram files
    if result["leftover_instagram"]:
        console.print(
            f"\n[yellow]Instagram files with no big match "
            f"({len(result['leftover_instagram'])} still in root):[/yellow]"
        )
        for f in result["leftover_instagram"][:20]:
            console.print(f"  [dim]{f}[/dim]")
        if len(result["leftover_instagram"]) > 20:
            console.print(f"  [dim]...and {len(result['leftover_instagram']) - 20} more[/dim]")

    return result
