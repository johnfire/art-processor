"""
Daily automated social media posting system.
Posts one random painting per day to all configured platforms.
Uses rounds logic to ensure all paintings are posted before repeating.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any

from rich.console import Console

console = Console()

# List of platforms for daily posting
DAILY_PLATFORMS = [
    "mastodon",
    "bluesky",
    "instagram",
    "threads",
    "cara",
    "pixelfed",
    "tiktok",
    "facebook",
    "linkedin",
]


def find_all_painting_metadata(metadata_path: Path) -> List[Tuple[Path, Dict[str, Any]]]:
    """
    Find all painting metadata files across all folders.

    Args:
        metadata_path: Root metadata directory

    Returns:
        List of (metadata_file_path, metadata_dict) tuples
    """
    results = []
    for json_file in metadata_path.rglob("*.json"):
        # Skip non-painting metadata files
        if json_file.name in ("upload_status.json", "schedule.json", "rounds.json"):
            continue

        try:
            with open(json_file, "r") as f:
                metadata = json.load(f)

            # Verify it's a painting metadata file
            if "filename_base" in metadata:
                results.append((json_file, metadata))
        except (json.JSONDecodeError, KeyError):
            continue

    return results


def get_current_round(metadata_path: Path) -> int:
    """
    Get the current posting round number.

    Args:
        metadata_path: Root metadata directory

    Returns:
        Current round number (starts at 1)
    """
    rounds_file = metadata_path / "rounds.json"

    if not rounds_file.exists():
        # Initialize rounds file
        rounds_data = {"current_round": 1}
        with open(rounds_file, "w") as f:
            json.dump(rounds_data, f, indent=2)
        return 1

    with open(rounds_file, "r") as f:
        rounds_data = json.load(f)

    return rounds_data.get("current_round", 1)


def increment_round(metadata_path: Path):
    """Increment the current round number."""
    rounds_file = metadata_path / "rounds.json"
    current_round = get_current_round(metadata_path)

    rounds_data = {"current_round": current_round + 1}
    with open(rounds_file, "w") as f:
        json.dump(rounds_data, f, indent=2)

    console.print(f"[green]✓ Incremented to round {current_round + 1}[/green]")


def find_eligible_paintings(
    all_paintings: List[Tuple[Path, Dict[str, Any]]],
    current_round: int,
    platforms: List[str]
) -> List[Tuple[Path, Dict[str, Any]]]:
    """
    Find paintings eligible for posting in the current round.
    A painting is eligible if ANY platform has post_count < current_round.

    Args:
        all_paintings: List of all painting metadata
        current_round: Current round number
        platforms: List of platform names to check

    Returns:
        List of eligible (metadata_path, metadata) tuples
    """
    eligible = []

    for metadata_path, metadata in all_paintings:
        social_media = metadata.get("social_media", {})

        # Check if ANY platform needs posting for this round
        is_eligible = False
        for platform in platforms:
            platform_data = social_media.get(platform, {})
            post_count = platform_data.get("post_count", 0)

            if post_count < current_round:
                is_eligible = True
                break

        if is_eligible:
            eligible.append((metadata_path, metadata))

    return eligible


def ensure_short_description(
    metadata: Dict[str, Any],
    metadata_path: Path,
) -> str:
    """
    Ensure short_description exists in metadata. Generate if missing.

    Args:
        metadata: Painting metadata dictionary
        metadata_path: Path to metadata file

    Returns:
        Short description text
    """
    # Check if short_description already exists
    if metadata.get("short_description"):
        return metadata["short_description"]

    # Need to generate short description
    long_description = metadata.get("description", "")

    if not long_description:
        # No description at all - need to generate from image
        console.print("  [yellow]No description found - will generate from image[/yellow]")
        return None  # Will be handled by posting logic

    # Summarize long description to short
    console.print("  [yellow]Generating short description from long description...[/yellow]")

    from src.image_analyzer import ImageAnalyzer
    analyzer = ImageAnalyzer()

    short_desc = analyzer.summarize_to_short_description(
        long_description,
        max_chars=200
    )

    # Save to metadata
    metadata["short_description"] = short_desc

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    console.print(f"  [green]Generated and saved short description ({len(short_desc)} chars)[/green]")

    return short_desc


def get_image_path(metadata: Dict[str, Any]) -> Path:
    """
    Get the image path for posting (prefer instagram version).

    Args:
        metadata: Painting metadata dictionary

    Returns:
        Path to image file, or None if not found
    """
    from config.settings import PAINTINGS_INSTAGRAM_PATH, PAINTINGS_BIG_PATH

    filename_base = metadata.get("filename_base", "")
    # Use collection_folder if available, otherwise fall back to category
    collection_folder = metadata.get("collection_folder") or metadata.get("category", "")

    # Try instagram version first (smaller file, optimized for social media)
    instagram = metadata.get("files", {}).get("instagram")
    if instagram:
        # Handle both list and string
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
    big = metadata.get("files", {}).get("big")
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

    # ONLY use big version if instagram truly doesn't exist
    # Skip big files to avoid Claude API size limits (5MB max)
    return None


def post_to_all_platforms(
    metadata_path: Path,
    metadata: Dict[str, Any],
    platforms: List[str],
    current_round: int,
) -> Dict[str, Any]:
    """
    Post painting to all platforms and update metadata.

    Args:
        metadata_path: Path to metadata file
        metadata: Painting metadata
        platforms: List of platform names
        current_round: Current round number

    Returns:
        Dict with success/failure counts and details
    """
    from src.social import get_platform
    from src.social.formatter import format_post_text

    title = metadata.get("title", {}).get("selected", "Untitled")
    results = {"succeeded": [], "failed": [], "warnings": []}

    # Get image
    image_path = get_image_path(metadata)
    if not image_path:
        console.print(f"  [red]No image file found - aborting[/red]")
        return {"succeeded": [], "failed": platforms, "warnings": ["No image file"]}

    # Ensure short description exists
    short_desc = ensure_short_description(metadata, metadata_path)

    # If still no description, generate from image
    if not short_desc:
        from src.image_analyzer import ImageAnalyzer
        analyzer = ImageAnalyzer()
        short_desc = analyzer.generate_social_description(image_path, title, max_chars=200)
        metadata["short_description"] = short_desc

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    # Temporarily set description for formatting (formatter uses 'description' field)
    original_desc = metadata.get("description")
    metadata["description"] = short_desc

    # Format post text
    text = format_post_text(metadata, max_words=75)

    # Restore original description
    if original_desc:
        metadata["description"] = original_desc

    # Initialize social_media dict if needed
    if "social_media" not in metadata:
        metadata["social_media"] = {}

    # Post to each platform
    for platform_name in platforms:
        try:
            platform = get_platform(platform_name)

            # Skip if not configured (stub)
            if platform._is_stub or not platform.is_configured():
                console.print(f"  [dim]{platform.display_name}: Skipped (not configured)[/dim]")
                results["warnings"].append(f"{platform.display_name} not configured")
                # Still mark as posted to keep counts in sync
                _update_platform_metadata(metadata, platform_name, current_round, None)
                continue

            # Verify credentials
            if not platform.verify_credentials():
                console.print(f"  [red]{platform.display_name}: Invalid credentials[/red]")
                results["failed"].append(platform_name)
                results["warnings"].append(f"{platform.display_name} credentials invalid")
                from src.social.post_logger import log_credential_failure
                log_credential_failure(platform_name)
                continue

            # Post
            console.print(f"  [cyan]Posting to {platform.display_name}...[/cyan]")
            alt_text = metadata.get("description", "")  # Use full description as alt text
            result = platform.post_image(image_path, text, alt_text)

            if result.success:
                console.print(f"  [green]✓ {platform.display_name} posted[/green]")
                _update_platform_metadata(metadata, platform_name, current_round, result.post_url)
                results["succeeded"].append(platform_name)
                from src.social.post_logger import log_post_success
                log_post_success(platform_name, title, image_path, result.post_url)
            else:
                console.print(f"  [red]✗ {platform.display_name} failed: {result.error}[/red]")
                results["failed"].append(platform_name)
                results["warnings"].append(f"{platform.display_name}: {result.error}")
                from src.social.post_logger import log_post_failure
                log_post_failure(platform_name, title, image_path, result.error)

        except Exception as e:
            console.print(f"  [red]✗ {platform.display_name} error: {e}[/red]")
            results["failed"].append(platform_name)
            results["warnings"].append(f"{platform.display_name}: {str(e)}")
            from src.social.post_logger import log_post_failure
            log_post_failure(platform_name, title, image_path, str(e))

    # Save updated metadata
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return results


def _update_platform_metadata(
    metadata: Dict[str, Any],
    platform_name: str,
    current_round: int,
    post_url: str = None,
):
    """Update metadata for a specific platform after posting."""
    if "social_media" not in metadata:
        metadata["social_media"] = {}

    if platform_name not in metadata["social_media"]:
        metadata["social_media"][platform_name] = {}

    platform_data = metadata["social_media"][platform_name]

    # Update post count to current round
    platform_data["post_count"] = current_round

    # Update last posted date
    platform_data["last_posted"] = datetime.now().isoformat()

    # Update URL if provided
    if post_url:
        platform_data["post_url"] = post_url


def run_daily_post(metadata_path: Path) -> bool:
    """
    Main function to run daily automated posting.

    Args:
        metadata_path: Root metadata directory

    Returns:
        True if successful, False otherwise
    """
    console.print("[bold cyan]Daily Automated Social Media Post[/bold cyan]\n")

    # Find all paintings
    all_paintings = find_all_painting_metadata(metadata_path)
    if not all_paintings:
        console.print("[red]No paintings found in metadata directory[/red]")
        return False

    console.print(f"Found {len(all_paintings)} total paintings")

    # Get current round
    current_round = get_current_round(metadata_path)
    console.print(f"Current round: {current_round}\n")

    # Find eligible paintings
    eligible = find_eligible_paintings(all_paintings, current_round, DAILY_PLATFORMS)

    if not eligible:
        console.print("[yellow]All paintings have been posted for this round![/yellow]")
        console.print("Incrementing to next round...\n")
        increment_round(metadata_path)

        # Try again with new round
        current_round = get_current_round(metadata_path)
        eligible = find_eligible_paintings(all_paintings, current_round, DAILY_PLATFORMS)

    if not eligible:
        console.print("[red]Still no eligible paintings - something is wrong[/red]")
        return False

    console.print(f"Eligible paintings for posting: {len(eligible)}\n")

    # Randomly select one
    metadata_path, metadata = random.choice(eligible)
    title = metadata.get("title", {}).get("selected", "Untitled")

    console.print(f"[bold]Selected painting:[/bold] {title}")
    console.print(f"[dim]File: {metadata_path.name}[/dim]\n")

    # Post to all platforms
    results = post_to_all_platforms(metadata_path, metadata, DAILY_PLATFORMS, current_round)

    # Print summary
    console.print("\n[bold]Results:[/bold]")
    console.print(f"  Succeeded: [green]{len(results['succeeded'])}[/green]")
    console.print(f"  Failed: [red]{len(results['failed'])}[/red]")

    if results["warnings"]:
        console.print(f"\n[yellow]Warnings:[/yellow]")
        for warning in results["warnings"]:
            console.print(f"  - {warning}")

    return True
