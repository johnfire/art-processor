"""
CLI functions for social media posting and scheduling.
Called from admin_mode.py and main.py.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table

console = Console()

_LOG_FILE = Path("~/.config/theo-van-gogh/social_post_log.txt").expanduser()


def _notify_post_success(title: str, platform_name: str, post_url: Optional[str]) -> None:
    """Log and send a desktop notification for a successful social media post."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url_part = f" — {post_url}" if post_url else ""
    log_line = f"[{timestamp}] Posted '{title}' to {platform_name}{url_part}\n"

    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOG_FILE, "a") as f:
        f.write(log_line)

    message = f"'{title}' posted to {platform_name}"
    if post_url:
        message += f"\n{post_url}"
    subprocess.run(
        ["notify-send", "--app-name=Theo van Gogh", "Social Media Post", message],
        check=False,
    )


def post_social_cli():
    """Interactive social media posting. Pick a platform, pick paintings, post."""
    from src.app.social import get_platform, get_all_platform_names
    from src.app.social.base import empty_social_media_dict
    from src.app.social.formatter import format_post_text
    from src.app.social.scheduler import _get_image_path, _update_social_media_tracking

    # Show available platforms
    all_names = get_all_platform_names()
    table = Table(title="Social Media Platforms")
    table.add_column("No.", style="dim", width=5)
    table.add_column("Platform")
    table.add_column("Status")

    configured = []
    for i, name in enumerate(all_names, 1):
        try:
            platform = get_platform(name)
            if platform._is_stub:
                table.add_row(str(i), platform.display_name, "[dim]Not yet implemented[/dim]")
            elif platform.is_configured():
                table.add_row(str(i), platform.display_name, "[green]Ready[/green]")
                configured.append((i, name, platform))
            else:
                table.add_row(str(i), platform.display_name, "[yellow]Not configured[/yellow]")
        except Exception:
            table.add_row(str(i), name, "[red]Error[/red]")

    console.print(table)

    if not configured:
        console.print("\n[yellow]No platforms are configured and ready.[/yellow]")
        console.print("[dim]Add credentials to your .env file to enable platforms.[/dim]")
        return

    # Pick platform
    valid_choices = [str(i) for i, _, _ in configured] + ["0"]
    choice = Prompt.ask(
        "\nSelect platform (0 to cancel)",
        choices=valid_choices,
        default="0"
    )
    if choice == "0":
        return

    idx = int(choice)
    platform_name = None
    platform = None
    for i, name, plat in configured:
        if i == idx:
            platform_name = name
            platform = plat
            break

    if not platform:
        return

    # Verify credentials
    console.print(f"\n[cyan]Verifying {platform.display_name} credentials...[/cyan]")
    try:
        ok = platform.verify_credentials()
    except Exception as e:
        console.print(f"[red]{platform.display_name} login error: {e}[/red]")
        return
    if not ok:
        console.print(f"[red]{platform.display_name} credentials are invalid. Check your .env file.[/red]")
        return
    console.print(f"[green]Authenticated with {platform.display_name}[/green]")

    # Find paintings not yet posted to this platform
    paintings = _find_unposted_paintings(platform_name)

    if not paintings:
        console.print(f"[yellow]No paintings pending for {platform.display_name}.[/yellow]")
        console.print("[dim]All paintings have been posted, or no metadata files found.[/dim]")
        return

    # Show pending paintings
    table = Table(title=f"Paintings to post to {platform.display_name}")
    table.add_column("No.", style="dim", width=5)
    table.add_column("Title")
    table.add_column("Posts", width=6)

    for i, (path, meta) in enumerate(paintings, 1):
        title = meta.get("title", {}).get("selected", path.stem)
        sm = meta.get("social_media", {}).get(platform_name, {})
        count = sm.get("post_count", 0)
        table.add_row(str(i), title, str(count))

    console.print(table)

    # Let user choose
    if len(paintings) == 1:
        if not Confirm.ask(f"Post to {platform.display_name}?", default=True):
            return
        to_post = paintings
    else:
        choices = ["all"] + [str(i) for i in range(1, len(paintings) + 1)] + ["0"]
        choice = Prompt.ask(
            "Post which? (number, 'all', or 0 to cancel)",
            choices=choices,
            default="0"
        )
        if choice == "0":
            return
        if choice == "all":
            to_post = paintings
        else:
            to_post = [paintings[int(choice) - 1]]

    # Post each painting
    succeeded = []
    failed = []

    for metadata_path, metadata in to_post:
        title = metadata.get("title", {}).get("selected", "Untitled")
        console.print(f"\n[cyan]Posting: {title}...[/cyan]")

        # Get image
        image_path = _get_image_path(metadata)
        if not image_path:
            console.print(f"  [red]No image file found — skipping[/red]")
            failed.append(title)
            continue

        # Check if description exists, generate if missing
        if not metadata.get("description"):
            console.print("  [yellow]No description found - generating social media description...[/yellow]")
            from src.app.services.image_analyzer import ImageAnalyzer
            analyzer = ImageAnalyzer()

            # Generate 200 character description
            short_desc = analyzer.generate_social_description(
                image_path,
                title,
                max_chars=200
            )

            # Update metadata
            metadata["description"] = short_desc

            # Save to file
            import json
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            console.print(f"  [green]Generated and saved description ({len(short_desc)} chars)[/green]")

        # Format post text
        text = format_post_text(metadata, max_words=75)

        # Preview
        console.print(f"\n[dim]Preview:[/dim]")
        console.print(f"[dim]{text}[/dim]")
        console.print(f"[dim]Image: {image_path}[/dim]\n")

        if not Confirm.ask("Post this?", default=True):
            console.print("  [yellow]Skipped[/yellow]")
            continue

        # Post
        alt_text = metadata.get("description") or ""
        result = platform.post_image(image_path, text, alt_text)

        if result.success:
            console.print(f"  [green]Posted![/green]")
            if result.post_url:
                console.print(f"  [dim]{result.post_url}[/dim]")
            _update_social_media_tracking(metadata_path, metadata, platform_name, result.post_url)
            succeeded.append(title)
            _notify_post_success(title, platform_name, result.post_url)
            from src.app.social.post_logger import log_post_success
            log_post_success(platform_name, title, image_path, result.post_url)
        else:
            console.print(f"  [red]Failed: {result.error}[/red]")
            console.print(f"  [dim]Failure logged to: ~/.config/theo-van-gogh/debug/logs/social.log[/dim]")
            failed.append(title)
            from src.app.social.post_logger import log_post_failure
            log_post_failure(platform_name, title, image_path, result.error)

    # Summary
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Posted: [green]{len(succeeded)}[/green]")
    if failed:
        console.print(f"  Failed: [red]{len(failed)}[/red]")


def schedule_post_cli():
    """Interactive scheduling of social media posts."""
    from src.app.social import get_platform, get_all_platform_names
    from src.app.social.scheduler import Scheduler

    # Pick platform
    all_names = get_all_platform_names()
    configured = []
    for name in all_names:
        try:
            platform = get_platform(name)
            if not platform._is_stub and platform.is_configured():
                configured.append((name, platform))
        except Exception:
            pass

    if not configured:
        console.print("[yellow]No platforms configured. Add credentials to .env first.[/yellow]")
        return

    console.print("\n[bold]Schedule a Post[/bold]\n")
    for i, (name, plat) in enumerate(configured, 1):
        console.print(f"  {i}. {plat.display_name}")

    choice = IntPrompt.ask(
        "Select platform",
        choices=[str(i) for i in range(1, len(configured) + 1)]
    )
    platform_name, platform = configured[choice - 1]

    # Pick painting
    paintings = _find_unposted_paintings(platform_name)
    if not paintings:
        console.print(f"[yellow]No paintings available for {platform.display_name}.[/yellow]")
        return

    for i, (path, meta) in enumerate(paintings, 1):
        title = meta.get("title", {}).get("selected", path.stem)
        console.print(f"  {i}. {title}")

    p_choice = IntPrompt.ask(
        "Select painting",
        choices=[str(i) for i in range(1, len(paintings) + 1)]
    )
    metadata_path, metadata = paintings[p_choice - 1]

    # Get date/time
    date_str = Prompt.ask("Date and time (YYYY-MM-DD HH:MM)", default="")
    if not date_str:
        console.print("[yellow]Cancelled[/yellow]")
        return

    try:
        scheduled_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except ValueError:
        console.print("[red]Invalid date format. Use YYYY-MM-DD HH:MM[/red]")
        return

    if scheduled_time <= datetime.now():
        console.print("[red]Scheduled time must be in the future.[/red]")
        return

    # Schedule it
    scheduler = Scheduler()
    post_id = scheduler.add_post(
        content_id=metadata.get("filename_base", metadata_path.stem),
        metadata_path=str(metadata_path),
        platform=platform_name,
        scheduled_time=scheduled_time.isoformat(),
    )

    title = metadata.get("title", {}).get("selected", "Untitled")
    console.print(f"\n[green]Scheduled: '{title}' to {platform.display_name}[/green]")
    console.print(f"[dim]Time: {scheduled_time.strftime('%Y-%m-%d %H:%M')} | ID: {post_id}[/dim]")


def view_schedule_cli():
    """Display upcoming and recent scheduled posts."""
    from src.app.social.scheduler import Scheduler

    scheduler = Scheduler()
    upcoming = scheduler.get_upcoming()
    history = scheduler.get_history(limit=20)

    if upcoming:
        table = Table(title="Upcoming Scheduled Posts")
        table.add_column("ID", style="dim", width=10)
        table.add_column("Platform")
        table.add_column("Painting")
        table.add_column("Scheduled Time")

        for post in sorted(upcoming, key=lambda p: p["scheduled_time"]):
            table.add_row(
                post["id"],
                post["platform"],
                post["content_id"],
                post["scheduled_time"][:16].replace("T", " "),
            )
        console.print(table)
    else:
        console.print("[dim]No upcoming scheduled posts.[/dim]")

    if history:
        console.print()
        table = Table(title="Recent Post History")
        table.add_column("Platform")
        table.add_column("Painting")
        table.add_column("Status")
        table.add_column("Time")

        for post in history:
            status_str = (
                "[green]Posted[/green]" if post["status"] == "posted"
                else f"[red]Failed: {post.get('error', '?')}[/red]"
            )
            table.add_row(
                post["platform"],
                post["content_id"],
                status_str,
                post["scheduled_time"][:16].replace("T", " "),
            )
        console.print(table)

    # Option to cancel
    if upcoming:
        if Confirm.ask("\nCancel a scheduled post?", default=False):
            post_id = Prompt.ask("Enter post ID to cancel")
            if scheduler.cancel_post(post_id):
                console.print(f"[green]Cancelled post {post_id}[/green]")
            else:
                console.print(f"[red]Post {post_id} not found or already executed[/red]")


def check_schedule_cli():
    """Execute pending scheduled posts. Designed for cron job."""
    from src.app.social.scheduler import Scheduler

    scheduler = Scheduler()
    pending = scheduler.get_pending()

    if not pending:
        return

    console.print(f"[cyan]Executing {len(pending)} scheduled post(s)...[/cyan]")
    results = scheduler.execute_pending()

    if results["posted"]:
        console.print(f"[green]Posted: {results['posted']}[/green]")
    if results["failed"]:
        console.print(f"[red]Failed: {results['failed']}[/red]")


def _find_unposted_paintings(platform_name: str) -> list:
    """Find all metadata files for paintings not yet posted to a platform."""
    from config.settings import METADATA_OUTPUT_PATH

    results = []
    for json_file in METADATA_OUTPUT_PATH.rglob("*.json"):
        if json_file.name in ("upload_status.json", "schedule.json"):
            continue
        try:
            with open(json_file, "r") as f:
                metadata = json.load(f)
            if "filename_base" not in metadata:
                continue
            # Check if not yet posted
            sm = metadata.get("social_media", {})
            entry = sm.get(platform_name, {})
            if entry.get("post_count", 0) == 0:
                results.append((json_file, metadata))
        except (json.JSONDecodeError, KeyError):
            continue

    return sorted(results, key=lambda x: x[1].get("title", {}).get("selected", ""))
