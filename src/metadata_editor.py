"""
Metadata editor module.
Allows users to browse and edit metadata files interactively.
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.table import Table
from rich.panel import Panel

from config.settings import (
    METADATA_OUTPUT_PATH,
    SUBSTRATES,
    MEDIUMS,
    SUBJECTS,
    STYLES,
    COLLECTIONS,
    DIMENSION_UNIT,
)
from src.metadata_manager import MetadataManager

console = Console()


class MetadataEditor:
    """Interactive editor for metadata JSON files."""

    def __init__(self, metadata_path: Path = METADATA_OUTPUT_PATH):
        self.metadata_path = metadata_path
        self.metadata_mgr = MetadataManager()
        self.console = console

    def list_subfolders(self) -> List[str]:
        """List subfolders in processed-metadata that contain JSON files."""
        folders = []
        if not self.metadata_path.exists():
            return folders

        for item in sorted(self.metadata_path.iterdir()):
            if not item.is_dir() or item.name.startswith("."):
                continue
            json_files = list(item.glob("*.json"))
            if json_files:
                folders.append(item.name)

        return folders

    def list_metadata_files(self, subfolder: str) -> List[Tuple[str, str, bool]]:
        """
        List metadata files in a subfolder.

        Returns:
            List of (filename_base, title, is_skeleton) tuples
        """
        folder_path = self.metadata_path / subfolder
        files = []

        for json_file in sorted(folder_path.glob("*.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            filename_base = json_file.stem
            title = data.get("title", {}).get("selected", filename_base)
            is_skeleton = data.get("is_skeleton", False)
            files.append((filename_base, title, is_skeleton))

        return files

    def _show_current_metadata(self, metadata: dict):
        """Display current metadata values in a panel."""
        dims = metadata.get("dimensions", {}) or {}
        formatted_dims = dims.get("formatted") or "Not set"

        files_big = metadata.get("files", {}).get("big")
        if isinstance(files_big, list):
            files_str = "\n".join(f"  {p}" for p in files_big)
        elif files_big:
            files_str = f"  {files_big}"
        else:
            files_str = "  Not set"

        description = metadata.get("description") or "Not set"
        if description != "Not set" and len(description) > 120:
            description = description[:120] + "..."

        content = (
            f"[bold]{metadata.get('title', {}).get('selected', 'Untitled')}[/bold]\n\n"
            f"[dim]Category:[/dim]     {metadata.get('category', 'N/A')}\n"
            f"[dim]Substrate:[/dim]    {metadata.get('substrate') or '[red]Not set[/red]'}\n"
            f"[dim]Medium:[/dim]       {metadata.get('medium') or '[red]Not set[/red]'}\n"
            f"[dim]Subject:[/dim]      {metadata.get('subject') or '[red]Not set[/red]'}\n"
            f"[dim]Style:[/dim]        {metadata.get('style') or '[red]Not set[/red]'}\n"
            f"[dim]Collection:[/dim]   {metadata.get('collection') or '[red]Not set[/red]'}\n"
            f"[dim]Dimensions:[/dim]   {formatted_dims}\n"
            f"[dim]Price:[/dim]        {metadata.get('price_eur') or '[red]Not set[/red]'}\n"
            f"[dim]Date:[/dim]         {metadata.get('creation_date') or '[red]Not set[/red]'}\n"
            f"[dim]Description:[/dim]  {description}\n"
            f"[dim]Files (big):[/dim]\n{files_str}"
        )

        is_skeleton = metadata.get("is_skeleton", False)
        border = "yellow" if is_skeleton else "green"
        tag = " [SKELETON]" if is_skeleton else ""

        self.console.print(
            Panel(content, title=f"Current Metadata{tag}", border_style=border)
        )

    def _prompt_title(self, current: Optional[str]) -> str:
        """Prompt for title, showing current value."""
        self.console.print(f"\n[bold cyan]Title[/bold cyan]")
        if current:
            self.console.print(f"[dim]Current: {current}[/dim]")
        return Prompt.ask("Title", default=current or "")

    def _prompt_description(self, current: Optional[str]) -> Optional[str]:
        """Prompt for description, showing current preview."""
        self.console.print(f"\n[bold cyan]Description[/bold cyan]")
        if current:
            preview = current[:80] + "..." if len(current) > 80 else current
            self.console.print(f"[dim]Current: {preview}[/dim]")
            keep = Confirm.ask("Keep current description?", default=True)
            if keep:
                return current

        new_desc = Prompt.ask("Enter description (or press Enter to skip)", default="")
        return new_desc if new_desc else current

    def _prompt_select(
        self, field_name: str, options: List[str], current: Optional[str]
    ) -> Optional[str]:
        """
        Generic list selector with 'Keep current' option.

        Shows numbered options with current value marked.
        Option 0 = keep current value.
        """
        self.console.print(f"\n[bold cyan]{field_name}[/bold cyan]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column(field_name)

        current_display = current or "Not set"
        table.add_row("0", f"Keep current: [yellow]{current_display}[/yellow]")

        for i, option in enumerate(options, 1):
            marker = " [green]<-- current[/green]" if option == current else ""
            table.add_row(str(i), f"{option}{marker}")

        self.console.print(table)

        choices = [str(i) for i in range(len(options) + 1)]
        choice = IntPrompt.ask(f"Select {field_name.lower()}", default=0, choices=choices)

        if choice == 0:
            return current
        return options[choice - 1]

    def _prompt_dimensions(self, current_dims: Optional[dict]) -> dict:
        """Prompt for dimensions, using current values as defaults."""
        self.console.print(f"\n[bold cyan]Dimensions[/bold cyan]")

        dims = current_dims or {}
        cur_width = dims.get("width")
        cur_height = dims.get("height")
        cur_depth = dims.get("depth")
        cur_unit = dims.get("unit") or DIMENSION_UNIT

        if dims.get("formatted"):
            self.console.print(f"[dim]Current: {dims['formatted']}[/dim]")

        keep = Confirm.ask("Edit dimensions?", default=False if cur_width else True)
        if not keep:
            return dims

        unit = cur_unit
        width = FloatPrompt.ask(f"Width ({unit})", default=cur_width or 0.0)
        height = FloatPrompt.ask(f"Height ({unit})", default=cur_height or 0.0)
        depth = FloatPrompt.ask(
            f"Depth ({unit}) - enter 0 for flat works", default=cur_depth or 0.0
        )

        if depth > 0:
            formatted = f"{width}{unit} x {height}{unit} x {depth}{unit}"
        else:
            formatted = f"{width}{unit} x {height}{unit}"
            depth = None

        return {
            "width": width,
            "height": height,
            "depth": depth,
            "unit": unit,
            "formatted": formatted,
        }

    def _prompt_price(self, current: Optional[float]) -> Optional[float]:
        """Prompt for price with current as default."""
        self.console.print(f"\n[bold cyan]Price[/bold cyan]")
        if current is not None:
            self.console.print(f"[dim]Current: {current} EUR[/dim]")
        return FloatPrompt.ask("Price (EUR)", default=current or 0.0)

    def _prompt_creation_date(self, current: Optional[str]) -> Optional[str]:
        """Prompt for creation date with current as default."""
        self.console.print(f"\n[bold cyan]Creation Date[/bold cyan]")
        if current:
            self.console.print(f"[dim]Current: {current}[/dim]")
        date_str = Prompt.ask(
            "Creation date (YYYY-MM-DD)", default=current or ""
        )
        return date_str if date_str else current

    def edit_file(self, category: str, filename_base: str) -> bool:
        """
        Edit a single metadata file interactively.

        Returns:
            True if changes were saved
        """
        metadata = self.metadata_mgr.load_metadata(category, filename_base)

        self.console.print(f"\n[bold]Editing: {filename_base}[/bold]")
        self._show_current_metadata(metadata)

        if not Confirm.ask("\nEdit this file?", default=True):
            return False

        # Walk through each editable field
        metadata["title"]["selected"] = self._prompt_title(
            metadata.get("title", {}).get("selected")
        )

        metadata["description"] = self._prompt_description(
            metadata.get("description")
        )

        metadata["substrate"] = self._prompt_select(
            "Substrate", SUBSTRATES, metadata.get("substrate")
        )

        metadata["medium"] = self._prompt_select(
            "Medium", MEDIUMS, metadata.get("medium")
        )

        metadata["subject"] = self._prompt_select(
            "Subject", SUBJECTS, metadata.get("subject")
        )

        metadata["style"] = self._prompt_select(
            "Style", STYLES, metadata.get("style")
        )

        metadata["collection"] = self._prompt_select(
            "Collection", COLLECTIONS, metadata.get("collection")
        )

        metadata["dimensions"] = self._prompt_dimensions(
            metadata.get("dimensions")
        )

        metadata["price_eur"] = self._prompt_price(metadata.get("price_eur"))

        metadata["creation_date"] = self._prompt_creation_date(
            metadata.get("creation_date")
        )

        # If all key fields are filled, remove skeleton flag
        key_fields = ["substrate", "medium", "subject", "style", "collection"]
        if all(metadata.get(f) for f in key_fields):
            metadata.pop("is_skeleton", None)

        # Save
        self.metadata_mgr.save_metadata_json(metadata, category)
        self.console.print(f"\n[green]Saved {filename_base}.json[/green]")
        return True

    def edit_all_in_folder(self, category: str) -> Tuple[int, int]:
        """
        Edit all metadata files in a folder sequentially.

        Returns:
            Tuple of (edited_count, skipped_count)
        """
        files = self.list_metadata_files(category)
        edited = 0
        skipped = 0

        for i, (filename_base, title, is_skeleton) in enumerate(files):
            self.console.print(
                f"\n[bold cyan]--- File {i + 1}/{len(files)} ---[/bold cyan]"
            )
            if self.edit_file(category, filename_base):
                edited += 1
            else:
                skipped += 1

            if i < len(files) - 1:
                if not Confirm.ask("Continue to next file?", default=True):
                    skipped += len(files) - i - 1
                    break

        return edited, skipped


def edit_metadata_cli() -> None:
    """CLI entry point for metadata editing. Called from admin mode."""
    editor = MetadataEditor()

    console.print("\n[bold cyan]Metadata Editor[/bold cyan]\n")

    # Step 1: Select subfolder
    folders = editor.list_subfolders()
    if not folders:
        console.print("[yellow]No metadata folders found.[/yellow]")
        return

    console.print("[bold]Select a folder:[/bold]")
    table = Table(show_header=False)
    table.add_column("No.", style="cyan", width=6)
    table.add_column("Folder")
    table.add_column("Files", justify="right")

    for i, folder in enumerate(folders, 1):
        file_count = len(editor.list_metadata_files(folder))
        table.add_row(str(i), folder, str(file_count))

    table.add_row("0", "Back", "")
    console.print(table)

    choices = [str(i) for i in range(len(folders) + 1)]
    folder_choice = IntPrompt.ask("Select folder", default=0, choices=choices)

    if folder_choice == 0:
        return

    category = folders[folder_choice - 1]
    files = editor.list_metadata_files(category)

    # Step 2: Edit all or select specific file
    console.print(f"\n[bold]Folder: {category}[/bold] ({len(files)} files)")

    mode_choice = IntPrompt.ask(
        "\n1. Edit all files\n2. Select a specific file\n0. Back\n\nSelect mode",
        default=1,
        choices=["0", "1", "2"],
    )

    if mode_choice == 0:
        return

    if mode_choice == 1:
        edited, skipped = editor.edit_all_in_folder(category)
        console.print(f"\n[bold]Done:[/bold] {edited} edited, {skipped} skipped")

    elif mode_choice == 2:
        # Show file list
        file_table = Table(show_header=True, header_style="bold magenta")
        file_table.add_column("No.", style="dim", width=6)
        file_table.add_column("Title")
        file_table.add_column("Status", justify="right")

        for i, (fb, title, is_skel) in enumerate(files, 1):
            status = "[yellow]skeleton[/yellow]" if is_skel else "[green]complete[/green]"
            file_table.add_row(str(i), title, status)

        file_table.add_row("0", "Back", "")
        console.print(file_table)

        file_choices = [str(i) for i in range(len(files) + 1)]
        file_choice = IntPrompt.ask("Select file", default=0, choices=file_choices)

        if file_choice == 0:
            return

        filename_base = files[file_choice - 1][0]
        editor.edit_file(category, filename_base)
