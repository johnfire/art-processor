"""
FASO artwork uploader - uploads paintings and fills metadata forms.
Uses persistent browser profile from manual_login.py (no automated login needed).
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from src.app.galleries.browser_uploader import BaseBrowserUploader

console = Console()


class FASOUploader(BaseBrowserUploader):
    """Handles uploading artwork to FASO with metadata."""

    name = "faso"

    @property
    def profile_dir(self) -> Path:
        from config.settings import COOKIES_DIR
        return COOKIES_DIR / "faso_browser_profile"

    @property
    def dashboard_url(self) -> str:
        return "https://data.fineartstudioonline.com/cfgeditwebsite.asp?new_login=y&faso_com_auth=y"

    async def upload_painting(self, metadata: Dict[str, Any]) -> bool:
        """
        Upload a single painting to FASO.

        Args:
            metadata: Full metadata dict loaded from JSON file.

        Returns:
            True on success, False on failure.
        """
        title = metadata.get("title", {}).get("selected", "Unknown")
        console.print(f"\n[bold cyan]Uploading: {title}[/bold cyan]")
        self._logger.info("Starting FASO upload for '%s'", title)

        if not await self._navigate_to_upload_page():
            return False

        image_path = self.get_image_path(metadata)
        if not image_path or not Path(image_path).exists():
            console.print(f"[red]Image file not found: {image_path}[/red]")
            return False

        if not await self._upload_image_file(image_path):
            return False

        if not await self._wait_for_upload_success():
            return False

        if not await self._click_continue():
            return False

        if not await self._fill_metadata_form(metadata):
            return False

        if not await self._save_form():
            return False

        console.print(f"[bold green]Successfully uploaded: {title}[/bold green]")
        self._logger.info("FASO upload complete for '%s'", title)
        return True

    async def _navigate_to_upload_page(self) -> bool:
        """Click 'Upload Art Now' to get to the upload page."""
        try:
            await self.page.goto(self.dashboard_url)
            await self.page.wait_for_load_state("networkidle")

            upload_btn = await self.page.wait_for_selector(
                'a.tb_link:has(img[src*="upload_2"])', timeout=30000
            )
            await upload_btn.click()
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            console.print("[green]On upload page[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Could not navigate to upload page: {e}[/red]")
            self._logger.error("Could not navigate to FASO upload page: %s", e)
            await self._take_error_screenshot("navigate")
            return False

    async def _upload_image_file(self, file_path: str) -> bool:
        """Upload an image file to FASO."""
        try:
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(file_path)
            else:
                async with self.page.expect_file_chooser() as fc_info:
                    upload_area = await self.page.wait_for_selector(
                        "text=Select Files to Upload", timeout=5000
                    )
                    await upload_area.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(file_path)

            await asyncio.sleep(2)

            upload_btn = await self.page.wait_for_selector(
                'span[data-e2e="upload"]', timeout=5000
            )
            await upload_btn.click()

            console.print("[cyan]Image uploading...[/cyan]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to upload image: {e}[/red]")
            self._logger.error("Failed to upload image file: %s", e)
            await self._take_error_screenshot("upload_image")
            return False

    async def _wait_for_upload_success(self) -> bool:
        """Wait for the 'Upload succeeded' confirmation."""
        try:
            await self.page.wait_for_selector("text=Upload succeeded", timeout=60000)
            console.print("[green]Image upload succeeded[/green]")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            console.print(f"[red]Upload did not complete in time: {e}[/red]")
            self._logger.error("FASO upload timed out waiting for confirmation: %s", e)
            await self._take_error_screenshot("upload_wait")
            return False

    async def _click_continue(self) -> bool:
        """Click the Continue button after upload success."""
        try:
            continue_btn = await self.page.wait_for_selector(
                'a:has-text("Continue"), button:has-text("Continue")', timeout=5000
            )
            await continue_btn.click()
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            console.print("[green]On metadata form[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Could not click Continue: {e}[/red]")
            self._logger.error("Could not click Continue after upload: %s", e)
            await self._take_error_screenshot("continue")
            return False

    async def _fill_metadata_form(self, metadata: Dict[str, Any]) -> bool:
        """Fill in all metadata form fields."""
        try:
            title = metadata.get("title", {}).get("selected", "")
            if title:
                await self._fill_text_field('input[name="Title"]', title)

            collection = metadata.get("collection")
            if collection:
                await self._select_dropdown_fuzzy('select[name="Collection"]', collection)

            medium = metadata.get("medium")
            if medium:
                await self._select_dropdown_fuzzy('select[name="Medium"]', medium)

            substrate = metadata.get("substrate")
            if substrate:
                await self._select_dropdown_fuzzy('select[name="Substrate"]', substrate)

            dims = metadata.get("dimensions", {})
            height = dims.get("height")
            width = dims.get("width")
            depth = dims.get("depth")

            if height is not None:
                await self._fill_text_field('input[name="VerticalSize"]', str(height))
            if width is not None:
                await self._fill_text_field('input[name="HorizontalSize"]', str(width))
            if depth is not None:
                await self._fill_text_field('input[name="Depth"]', str(depth))

            creation_date = metadata.get("creation_date")
            year = self.extract_year(creation_date)
            if year:
                await self._select_dropdown('select[name="YearCreated"]', year)

            subject = metadata.get("subject")
            if subject:
                await self._select_dropdown_fuzzy('select[name="Subject"]', subject)

            style = metadata.get("style")
            if style:
                await self._select_dropdown_fuzzy('select[name="Style"]', style)

            price = metadata.get("price_eur")
            if price is not None:
                await self._fill_text_field('input[name="RetailPrice"]', str(int(price)))

            await self._select_dropdown('select[name="Availability"]', "Available")

            description = metadata.get("description")
            if description:
                await self._fill_description(description)

            console.print("[green]Form fields filled[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Error filling form: {e}[/red]")
            self._logger.error("Error filling FASO metadata form: %s", e)
            await self._take_error_screenshot("fill_form")
            return False

    async def _save_form(self) -> bool:
        """Click Save Changes."""
        try:
            save_btn = await self.page.wait_for_selector(
                'input[value*="Save Changes"]', timeout=5000
            )
            await save_btn.click()
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            console.print("[green]Changes saved[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Could not save form: {e}[/red]")
            self._logger.error("Could not save FASO form: %s", e)
            await self._take_error_screenshot("save")
            return False

    @staticmethod
    def is_upload_ready(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if metadata has all required fields for FASO upload.

        Returns:
            (is_ready, list_of_missing_field_names)
        """
        missing = []

        if not metadata.get("title", {}).get("selected"):
            missing.append("title")

        big_path = metadata.get("files", {}).get("big")
        if not big_path:
            missing.append("image file path")
        else:
            path = big_path[0] if isinstance(big_path, list) else big_path
            if not Path(path).exists():
                missing.append(f"image file missing: {Path(path).name}")

        for field in ["medium", "substrate", "subject", "style", "collection"]:
            if not metadata.get(field):
                missing.append(field)

        dims = metadata.get("dimensions", {})
        if not dims.get("width") or not dims.get("height"):
            missing.append("dimensions")

        if not metadata.get("description"):
            missing.append("description")

        return (len(missing) == 0, missing)


async def _do_uploads(
    paintings: List[Tuple[str, Dict[str, Any]]],
) -> Tuple[List[str], List[str]]:
    """Run the actual browser uploads. Returns (succeeded_filenames, failed_filenames)."""
    succeeded = []
    failed = []

    async with FASOUploader(headless=False) as uploader:
        if not await uploader.start_browser():
            return succeeded, failed

        for filename, metadata in paintings:
            success = await uploader.upload_painting(metadata)

            if success:
                succeeded.append(filename)
            else:
                failed.append(filename)

            if paintings.index((filename, metadata)) < len(paintings) - 1:
                await asyncio.sleep(2)

    return succeeded, failed


def _find_all_metadata_files() -> list:
    """Scan processed-metadata for all JSON metadata files."""
    from config.settings import METADATA_OUTPUT_PATH
    results = []
    for json_file in METADATA_OUTPUT_PATH.rglob("*.json"):
        if json_file.name in ("upload_status.json", "schedule.json"):
            continue
        try:
            with open(json_file, "r") as f:
                metadata = json.load(f)
            if "filename_base" in metadata:
                results.append((json_file, metadata))
        except (json.JSONDecodeError, KeyError):
            continue
    return results


def _is_faso_pending(metadata: dict) -> bool:
    """Check if a painting has not been uploaded to FASO."""
    gallery_sites = metadata.get("gallery_sites", {})
    faso = gallery_sites.get("faso", {})
    return faso.get("last_uploaded") is None


def _mark_faso_uploaded(metadata_path: Path, metadata: dict):
    """Update gallery_sites.faso.last_uploaded in metadata JSON."""
    if "gallery_sites" not in metadata:
        from src.app.galleries.base import empty_gallery_sites_dict
        metadata["gallery_sites"] = empty_gallery_sites_dict()
    if "faso" not in metadata["gallery_sites"]:
        from src.app.galleries.base import default_gallery_entry
        metadata["gallery_sites"]["faso"] = default_gallery_entry()

    metadata["gallery_sites"]["faso"]["last_uploaded"] = datetime.now().isoformat()

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def upload_faso_cli():
    """CLI entry point for FASO upload. Called from admin mode or CLI command."""
    all_metadata = _find_all_metadata_files()
    pending = [
        (path, meta) for path, meta in all_metadata
        if _is_faso_pending(meta)
    ]

    if not pending:
        console.print("[yellow]No paintings pending FASO upload.[/yellow]")
        return

    ready_paintings = []
    not_ready = []

    for metadata_path, metadata in pending:
        filename = metadata.get("filename_base", metadata_path.stem)
        try:
            is_ready, missing = FASOUploader.is_upload_ready(metadata)
            if is_ready:
                ready_paintings.append((filename, metadata, metadata_path))
            else:
                not_ready.append((filename, missing))
        except Exception as e:
            not_ready.append((filename, [str(e)]))

    table = Table(title="Pending FASO Uploads")
    table.add_column("No.", style="dim", width=5)
    table.add_column("Title")
    table.add_column("Status")

    for i, (filename, metadata, _) in enumerate(ready_paintings, 1):
        title = metadata.get("title", {}).get("selected", filename)
        table.add_row(str(i), title, "[green]Ready[/green]")

    for filename, missing in not_ready:
        table.add_row("-", filename, f"[red]Missing: {', '.join(missing)}[/red]")

    console.print(table)

    if not ready_paintings:
        console.print("[yellow]No paintings are ready for upload.[/yellow]")
        return

    console.print(f"\n[bold]{len(ready_paintings)} painting(s) ready for upload[/bold]")

    if len(ready_paintings) == 1:
        if not Confirm.ask(
            f"Upload '{ready_paintings[0][1]['title']['selected']}' to FASO?",
            default=True,
        ):
            return
        choice = "1"
    else:
        choices = ["all"] + [str(i) for i in range(1, len(ready_paintings) + 1)] + ["0"]
        choice = Prompt.ask(
            "Upload which? (number, 'all', or 0 to cancel)",
            choices=choices,
            default="all",
        )
        if choice == "0":
            return

    if choice == "all":
        to_upload = ready_paintings
    else:
        idx = int(choice) - 1
        to_upload = [ready_paintings[idx]]

    if len(to_upload) > 1:
        if not Confirm.ask(f"Upload {len(to_upload)} painting(s) to FASO?", default=True):
            return

    upload_pairs = [(fn, meta) for fn, meta, _ in to_upload]
    console.print("\n[cyan]Starting browser for upload...[/cyan]")
    succeeded, failed = asyncio.run(_do_uploads(upload_pairs))

    console.print(f"\n[bold]Upload Results:[/bold]")
    console.print(f"  Succeeded: [green]{len(succeeded)}[/green]")
    if failed:
        console.print(f"  Failed: [red]{len(failed)}[/red]")

    if succeeded:
        console.print(f"\n[bold]Mark uploads as complete?[/bold]")
        console.print("[dim]You can re-upload later if you don't mark them now.[/dim]")

        path_lookup = {fn: mp for fn, _, mp in to_upload}

        for filename in succeeded:
            if Confirm.ask(f"  Mark '{filename}' as uploaded?", default=True):
                mp = path_lookup.get(filename)
                if mp:
                    with open(mp, "r") as f:
                        meta = json.load(f)
                    _mark_faso_uploaded(mp, meta)
                console.print(f"    [green]Marked done[/green]")
            else:
                console.print(f"    [yellow]Kept pending (can re-upload)[/yellow]")
