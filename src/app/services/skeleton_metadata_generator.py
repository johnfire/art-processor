"""
Skeleton metadata generator.
Scans painting folders and creates stub metadata JSON files for unprocessed paintings.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

from rich.console import Console
from rich.table import Table

from config.settings import (
    PAINTINGS_BIG_PATH,
    METADATA_OUTPUT_PATH,
    SUPPORTED_IMAGE_FORMATS,
)
from src.app.services.metadata_manager import MetadataManager

console = Console()


class SkeletonMetadataGenerator:
    """Scans painting folders and generates skeleton metadata files."""

    def __init__(
        self,
        big_path: Path = PAINTINGS_BIG_PATH,
        metadata_path: Path = METADATA_OUTPUT_PATH,
    ):
        self.big_path = big_path
        self.metadata_path = metadata_path
        self.metadata_mgr = MetadataManager()

    @staticmethod
    def extract_base_name(filename_stem: str) -> str:
        """
        Extract the base name by stripping a trailing numeric suffix.

        Only strips if the final dash-delimited segment is purely numeric.
        Examples:
            'Black-Palm-1'      -> 'Black-Palm'
            'Black-Palm-5'      -> 'Black-Palm'
            'QBits-5-A17'       -> 'QBits-5-A17'  (A17 not pure digits)
            'fractured_networks' -> 'fractured_networks'
            'Fire-Star'         -> 'Fire-Star'
        """
        match = re.match(r"^(.+)-(\d+)$", filename_stem)
        if match:
            return match.group(1)
        return filename_stem

    @staticmethod
    def filename_to_title(base_name: str) -> str:
        """
        Convert filename base name to a human-readable title.

        'mountain-sunset'    -> 'Mountain Sunset'
        'fractured_networks' -> 'Fractured Networks'
        """
        title = base_name.replace("-", " ").replace("_", " ")
        title = " ".join(title.split())
        return title.title()

    def scan_folder(self, category_path: Path) -> Dict[str, List[Path]]:
        """
        Scan a single category folder and group images by base name.

        Groups are case-insensitive so 'heavens-Bell' and 'Heavens-Bell'
        map to the same group.

        Returns:
            Dict mapping lowercase base_name -> list of file Paths
        """
        groups: Dict[str, List[Path]] = defaultdict(list)

        for file_path in category_path.iterdir():
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
                continue

            stem = file_path.stem
            base = self.extract_base_name(stem)
            group_key = base.lower()
            groups[group_key].append(file_path)

        return dict(groups)

    def generate_for_folder(
        self,
        category_name: str,
        groups: Dict[str, List[Path]],
    ) -> Tuple[int, int, List[str]]:
        """
        Generate skeleton metadata for all groups in a folder.

        Returns:
            Tuple of (created_count, skipped_count, errors)
        """
        created = 0
        skipped = 0
        errors = []

        for group_key, file_paths in sorted(groups.items()):
            # Use the first file's actual stem for display casing
            representative_stem = sorted(file_paths, key=lambda p: p.name.lower())[0].stem
            base_name = self.extract_base_name(representative_stem)

            # Build filename_base (lowercase, underscores) to match existing convention
            filename_base = group_key.replace("-", "_").replace(" ", "_")

            # Check if metadata already exists
            if self.metadata_mgr.metadata_exists(category_name, filename_base):
                skipped += 1
                continue

            title = self.filename_to_title(base_name)

            try:
                metadata = self.metadata_mgr.create_skeleton_metadata(
                    filename_base=filename_base,
                    category=category_name,
                    title=title,
                    big_file_paths=file_paths,
                )
                self.metadata_mgr.save_metadata_json(metadata, category_name)
                created += 1
            except Exception as e:
                errors.append(f"{base_name}: {e}")

        return created, skipped, errors

    def generate_all(self) -> dict:
        """
        Scan all category folders and generate skeleton metadata.

        Returns:
            Dict with results summary
        """
        total_created = 0
        total_skipped = 0
        total_errors = []
        folder_results = []

        if not self.big_path.exists():
            return {
                "total_created": 0,
                "total_skipped": 0,
                "errors": [f"Paintings path does not exist: {self.big_path}"],
                "folders": [],
            }

        for subfolder in sorted(self.big_path.iterdir()):
            if not subfolder.is_dir():
                continue
            if subfolder.name.startswith("."):
                continue

            category_name = subfolder.name
            groups = self.scan_folder(subfolder)

            if not groups:
                continue

            created, skipped, errors = self.generate_for_folder(
                category_name, groups
            )

            folder_results.append(
                {
                    "folder": category_name,
                    "images_found": sum(len(v) for v in groups.values()),
                    "groups_found": len(groups),
                    "created": created,
                    "skipped": skipped,
                    "errors": errors,
                }
            )

            total_created += created
            total_skipped += skipped
            total_errors.extend(errors)

        return {
            "total_created": total_created,
            "total_skipped": total_skipped,
            "errors": total_errors,
            "folders": folder_results,
        }


def generate_skeleton_metadata_cli() -> dict:
    """CLI entry point for skeleton metadata generation. Called from admin mode."""
    generator = SkeletonMetadataGenerator()

    console.print("\n[bold cyan]Skeleton Metadata Generator[/bold cyan]\n")
    console.print(f"Scanning: {generator.big_path}")
    console.print(f"Output:   {generator.metadata_path}\n")

    result = generator.generate_all()

    if result["folders"]:
        table = Table(title="Scan Results")
        table.add_column("Folder", style="cyan")
        table.add_column("Images", justify="right")
        table.add_column("Groups", justify="right")
        table.add_column("Created", justify="right", style="green")
        table.add_column("Skipped", justify="right", style="yellow")

        for fr in result["folders"]:
            table.add_row(
                fr["folder"],
                str(fr["images_found"]),
                str(fr["groups_found"]),
                str(fr["created"]),
                str(fr["skipped"]),
            )

        console.print(table)
    else:
        console.print("[yellow]No folders with images found.[/yellow]")

    console.print(
        f"\n[bold]Total created:[/bold] [green]{result['total_created']}[/green]"
    )
    console.print(
        f"[bold]Total skipped:[/bold] [yellow]{result['total_skipped']}[/yellow]"
    )

    if result["errors"]:
        console.print(f"\n[red]Errors ({len(result['errors'])}):[/red]")
        for err in result["errors"]:
            console.print(f"  [red]* {err}[/red]")

    return result
