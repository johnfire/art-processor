#!/usr/bin/env python3
"""
Theo-van-Gogh - Main CLI Entry Point
Orchestrates the complete painting processing workflow.
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Confirm

from src.app.services.image_analyzer import ImageAnalyzer
from src.app.services.file_manager import FileManager
from src.app.services.metadata_manager import MetadataManager
from src.app.services.cli_interface import CLIInterface
from src.app.services.admin_mode import AdminMode
from src.core.logger import configure_logging, get_logger
from config.settings import PAINTINGS_BIG_PATH, PAINTINGS_INSTAGRAM_PATH


console = Console()
configure_logging()
_log = get_logger("cli")


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Theo-van-Gogh - Automated painting metadata generation and management."""
    if ctx.invoked_subcommand is None:
        # Show admin mode option at startup
        console.print("\n[bold cyan]Theo-van-Gogh[/bold cyan]\n")
        
        if Confirm.ask("Enter admin mode?", default=False):
            settings_path = Path(__file__).parent / "config" / "settings.py"
            admin = AdminMode(settings_path)
            admin.run()
            console.print("\n")
        
        # After admin mode (or if skipped), show available commands
        console.print("Available commands:")
        console.print("  [cyan]python main.py process[/cyan]       - Process paintings")
        console.print("  [cyan]python main.py verify-config[/cyan]  - Verify configuration")
        console.print("  [cyan]python main.py admin[/cyan]          - Enter admin mode")
        console.print("  [cyan]python main.py upload-faso[/cyan]    - Upload to FASO")
        console.print("  [cyan]python main.py post-social[/cyan]   - Post to social media")
        console.print("  [cyan]python main.py schedule-post[/cyan]  - Schedule a post")
        console.print("  [cyan]python main.py check-schedule[/cyan] - Run scheduled posts")
        console.print("  [cyan]python main.py daily-post[/cyan]     - Daily automated posting")
        console.print("\nRun with --help for more information")


@cli.command()
def admin():
    """Enter admin mode to edit configuration settings."""
    settings_path = Path(__file__).parent / "config" / "settings.py"
    admin_mode = AdminMode(settings_path)
    admin_mode.run()


@cli.command()
def process():
    """
    Process all paintings in the new-paintings folder.
    
    Looks for paintings in: Pictures/my-paintings-big/new-paintings/
    
    Example:
        python main.py process
    """
    try:
        # Initialize components
        ui = CLIInterface()
        file_mgr = FileManager()
        analyzer = ImageAnalyzer()
        metadata_mgr = MetadataManager()
        
        ui.print_header("Theo-van-Gogh - Phase 1")
        
        # Hard-coded category
        category = "new-paintings"
        
        # Build full path to new-paintings folder
        new_paintings_path = PAINTINGS_BIG_PATH / category
        
        # Verify new-paintings folder exists
        if not new_paintings_path.exists():
            ui.print_error(f"New paintings folder not found: {new_paintings_path}")
            ui.print_info("Please create the folder: Pictures/my-paintings-big/new-paintings/")
            return
        
        ui.print_header(f"Processing Folder: {category}")
        
        # Find all paintings in new-paintings folder
        painting_pairs = file_mgr.find_painting_files(category)
        
        if not painting_pairs:
            ui.print_warning(f"No paintings found in {new_paintings_path}")
            ui.print_info("Place JPG files in Pictures/my-paintings-big/new-paintings/")
            return
        
        ui.print_info(f"Found {len(painting_pairs)} painting(s)")
        
        # Process each painting
        processed_filenames = []
        for big_file, instagram_file in painting_pairs:
            result = process_single_painting(
                big_file,
                instagram_file,
                category,
                ui,
                file_mgr,
                analyzer,
                metadata_mgr,
            )
            if result:  # If processing succeeded
                processed_filenames.append(result)
        
        ui.print_success(f"\nProcessing complete! Processed {len(processed_filenames)} painting(s)")
        
        # Step: Organize paintings into collection folders
        if processed_filenames:
            ui.print_header("\nOrganizing Paintings")
            ui.print_info("Moving paintings to collection folders...")
            
            from src.app.services.file_organizer import FileOrganizer
            from src.app.services.upload_tracker import UploadTracker
            from config.settings import METADATA_OUTPUT_PATH
            
            organizer = FileOrganizer(
                PAINTINGS_BIG_PATH,
                PAINTINGS_INSTAGRAM_PATH,
                METADATA_OUTPUT_PATH
            )
            
            results = organizer.organize_all_new_paintings()
            
            ui.print_success(f"\nOrganized {results['success']} of {results['processed']} paintings")
            
            if results['errors']:
                ui.print_warning(f"{len(results['errors'])} errors occurred:")
                for error in results['errors']:
                    ui.print_error(f"  {error}")
            
            # Step: Update upload tracker
            ui.print_info("\nUpdating upload tracker...")
            from config.settings import UPLOAD_TRACKER_PATH
            tracker = UploadTracker(UPLOAD_TRACKER_PATH)
            
            for filename in processed_filenames:
                metadata_file = METADATA_OUTPUT_PATH / "new-paintings" / f"{filename}.json"
                # After organizing, metadata is in collection folder
                # We need to find it
                import json
                for collection_folder in METADATA_OUTPUT_PATH.iterdir():
                    if collection_folder.is_dir():
                        candidate = collection_folder / f"{filename}.json"
                        if candidate.exists():
                            tracker.add_painting(filename, str(candidate))
                            break
            
            pending = tracker.get_all_pending()
            ui.print_success(f"\nUpload tracker updated")
            ui.print_info(f"Paintings pending upload:")
            for platform, paintings in pending.items():
                ui.print_info(f"  {platform}: {len(paintings)} painting(s)")
        
    except KeyboardInterrupt:
        ui.print_warning("\nProcessing interrupted by user")
        sys.exit(0)
    except Exception as e:
        ui.print_error(f"Error: {e}")
        _log.exception("process command failed")
        sys.exit(1)


def process_single_painting(
    big_file: Path,
    instagram_file: Path,
    category: str,
    ui: CLIInterface,
    file_mgr: FileManager,
    analyzer: ImageAnalyzer,
    metadata_mgr: MetadataManager,
) -> str:
    """
    Process a single painting through the complete workflow.
    
    Args:
        big_file: Path to big version
        instagram_file: Path to instagram version (or None)
        category: Category name
        ui: CLI interface
        file_mgr: File manager
        analyzer: Image analyzer
        metadata_mgr: Metadata manager
    """
    ui.print_header(f"\nProcessing: {big_file.name}")
    ui.show_file_info(big_file, instagram_file)
    
    # Check if already processed
    filename_stem = big_file.stem
    if metadata_mgr.metadata_exists(category, filename_stem):
        skip = not ui.confirm_processing(
            f"Metadata already exists for {big_file.name}. Reprocess?"
        )
        if skip:
            ui.print_info("Skipping")
            return None
    else:
        # Ask for confirmation
        if not ui.confirm_processing(big_file.name):
            ui.print_info("Skipping")
            return None
    
    try:
        # Import DIMENSION_UNIT from settings
        from config.settings import DIMENSION_UNIT
        
        # Determine which file to use for AI analysis
        # Prefer Instagram version (smaller), fallback to big if not available
        analyze_file = instagram_file if instagram_file and instagram_file.exists() else big_file
        
        if analyze_file == big_file and not instagram_file:
            ui.print_warning("No Instagram version found - using big version for analysis")
        
        # Step 1: Generate AI titles first
        ui.print_info("Generating AI titles...")
        ai_titles = analyzer.generate_titles(analyze_file)

        # Step 2: Show AI titles and let user select or enter custom
        selected_title, all_titles = ui.select_or_custom_title(ai_titles)

        # Step 2a: Get optional user notes about the painting
        user_notes = ui.input_painting_notes()

        # Step 3: User inputs dimensions manually (width, height, depth)
        width, height, depth, dimensions_formatted = ui.input_dimensions(unit=DIMENSION_UNIT)
        
        # Step 4: User selects substrate
        substrate = ui.select_substrate()
        
        # Step 5: User selects medium
        medium = ui.select_medium()
        
        # Step 6: User selects subject
        subject = ui.select_subject()
        
        # Step 7: User selects style
        style = ui.select_style()
        
        # Step 8: User selects collection
        collection = ui.select_collection()
        
        # Step 9: User inputs price
        price = ui.input_price(default=0.0)
        
        # Step 10: Get creation date
        suggested_date = file_mgr.get_creation_date(big_file)
        creation_date = ui.input_creation_date(suggested_date)
        
        # Step 11: Generate description
        ui.print_info("Generating description...")
        # Build full medium description for AI
        full_medium = f"{medium} on {substrate}"
        description = analyzer.generate_description(
            analyze_file,  # Use Instagram version for analysis
            selected_title,
            full_medium,
            dimensions_formatted,
            category,
            user_notes=user_notes,
        )
        
        # Step 12: Rename files
        ui.print_info("Renaming files...")
        sanitized_name = file_mgr.sanitize_filename(selected_title)
        new_big_path, new_instagram_path = file_mgr.rename_painting_pair(
            big_file,
            instagram_file,
            sanitized_name,
        )
        ui.print_success(f"Renamed to: {sanitized_name}{big_file.suffix}")
        
        # Step 13: Create metadata
        metadata = metadata_mgr.create_metadata(
            filename_base=sanitized_name,
            category=category,
            big_file_path=new_big_path,
            instagram_file_path=new_instagram_path,
            selected_title=selected_title,
            all_titles=all_titles,  # Changed from 'titles'
            description=description,
            width=width,
            height=height,
            depth=depth,
            dimension_unit=DIMENSION_UNIT,
            dimensions_formatted=dimensions_formatted,
            substrate=substrate,
            medium=medium,
            subject=subject,
            style=style,
            collection=collection,
            price_eur=price,
            creation_date=creation_date,
            analyzed_from="instagram" if analyze_file == instagram_file else "big",
        )
        
        # Step 14: Save metadata files
        json_path = metadata_mgr.save_metadata_json(metadata, category)
        txt_path = metadata_mgr.save_metadata_text(metadata, category)
        
        ui.print_success(f"Metadata saved: {json_path.name}")
        ui.print_success(f"Text file saved: {txt_path.name}")
        
        # Show summary
        ui.show_processing_summary(metadata)
        
        # Return filename for tracking
        return sanitized_name
        
    except Exception as e:
        ui.print_error(f"Error processing {big_file.name}: {e}")
        raise


@cli.command()
def list_categories():
    """List all available categories."""
    ui = CLIInterface()
    file_mgr = FileManager()
    
    categories = file_mgr.get_available_categories()
    
    if not categories:
        ui.print_warning("No categories found")
        return
    
    ui.print_header("Available Categories")
    for cat in categories:
        paintings = file_mgr.find_painting_files(cat)
        ui.print_info(f"{cat}: {len(paintings)} painting(s)")


@cli.command()
def verify_config():
    """Verify configuration and file paths."""
    ui = CLIInterface()
    
    ui.print_header("Configuration Verification")
    
    # Check API key
    #if ANTHROPIC_API_KEY:
    #    ui.print_success("✓ Anthropic API key configured")
    #else:
    #    ui.print_error("✗ Anthropic API key not found")
    
    # Check paths
    paths_ok = True
    for name, path in [
        ("Big paintings", PAINTINGS_BIG_PATH),
        ("Instagram paintings", PAINTINGS_INSTAGRAM_PATH),
    #    ("Metadata output", METADATA_OUTPUT_PATH),
    ]:
        if path.exists():
            ui.print_success(f"✓ {name}: {path}")
        else:
            ui.print_error(f"✗ {name} not found: {path}")
            paths_ok = False
    
    if paths_ok:
        ui.print_success("\n✓ All paths configured correctly")
    else:
        ui.print_warning("\n⚠ Some paths need to be created or configured")


@cli.command()
def test_faso_login():
    """Test FASO login and navigation (Phase 2)."""
    import asyncio
    from src.app.galleries.faso_client import test_faso_login
    from config.settings import FASO_EMAIL, FASO_PASSWORD
    
    ui = CLIInterface()
    ui.print_header("FASO Login Test")
    
    # Check credentials are configured
    try:
        if not FASO_EMAIL or not FASO_PASSWORD:
            ui.print_error("FASO credentials not configured in settings.py")
            ui.print_info("Add FASO_EMAIL and FASO_PASSWORD to config/settings.py")
            return
    except AttributeError:
        ui.print_error("FASO credentials not found in settings.py")
        ui.print_info("Add these lines to config/settings.py:")
        ui.print_info('FASO_EMAIL = os.getenv("FASO_EMAIL", "your-email@example.com")')
        ui.print_info('FASO_PASSWORD = os.getenv("FASO_PASSWORD", "your-password")')
        return
    
    ui.print_info(f"Testing login with: {FASO_EMAIL}")
    ui.print_info("Browser will open in visible mode...")
    ui.print_info("Watch the browser to see if login works!")
    
    # Run the async test
    success = asyncio.run(test_faso_login(FASO_EMAIL, FASO_PASSWORD))
    
    if success:
        ui.print_success("\n✓ FASO login test successful!")
    else:
        ui.print_error("\n✗ FASO login test failed")
        ui.print_info("Check debug screenshots: debug_*.png")


@cli.command()
def verify_config_old():
    """Verify configuration and paths."""
    ui = CLIInterface()
    
    ui.print_header("Configuration Verification")
    
    # Check paths
    checks = [
        ("Big paintings path", PAINTINGS_BIG_PATH),
        ("Instagram paintings path", PAINTINGS_INSTAGRAM_PATH),
    ]
    
    for name, path in checks:
        if path.exists():
            ui.print_success(f"{name}: {path}")
        else:
            ui.print_error(f"{name} not found: {path}")
    
    # Check API key
    from config.settings import ANTHROPIC_API_KEY
    if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your_api_key_here":
        ui.print_success("Anthropic API key: configured")
    else:
        ui.print_error("Anthropic API key: NOT configured")
        ui.print_info("Set ANTHROPIC_API_KEY in your .env file")


@cli.command()
def upload_faso():
    """Upload artwork to FASO (Fine Art Studio Online)."""
    from src.app.galleries.faso_uploader import upload_faso_cli

    ui = CLIInterface()
    ui.print_header("FASO Upload")

    try:
        upload_faso_cli()
    except KeyboardInterrupt:
        ui.print_warning("\nUpload interrupted by user")
    except Exception as e:
        ui.print_error(f"Error: {e}")
        _log.exception("upload-faso command failed")


@cli.command()
def post_social():
    """Post artwork to social media platforms."""
    from src.app.social.cli import post_social_cli
    from src.app.services.activity_log import log_activity

    ui = CLIInterface()
    ui.print_header("Social Media Post")
    log_activity("CLI: post-social")

    try:
        post_social_cli()
    except KeyboardInterrupt:
        ui.print_warning("\nPosting interrupted by user")
    except Exception as e:
        ui.print_error(f"Error: {e}")
        _log.exception("post-social command failed")


@cli.command()
def cara_login():
    """Set up persistent Cara browser session (run once before posting)."""
    from src.app.social.cara import CaraPlatform

    ui = CLIInterface()
    ui.print_header("Cara Login Setup")

    try:
        platform = CaraPlatform()
        platform.setup_session()
    except KeyboardInterrupt:
        ui.print_warning("\nLogin setup cancelled")
    except Exception as e:
        ui.print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()


@cli.command()
def schedule_post():
    """Schedule a future social media post."""
    from src.app.social.cli import schedule_post_cli

    ui = CLIInterface()
    ui.print_header("Schedule Post")

    try:
        schedule_post_cli()
    except KeyboardInterrupt:
        ui.print_warning("\nScheduling interrupted by user")
    except Exception as e:
        ui.print_error(f"Error: {e}")
        _log.exception("schedule-post command failed")


@cli.command()
def check_schedule():
    """Execute pending scheduled posts (designed for cron job)."""
    from src.app.social.cli import check_schedule_cli
    from src.app.services.activity_log import log_activity

    log_activity("CLI: check-schedule")
    try:
        check_schedule_cli()
    except Exception as e:
        console.print(f"[red]Schedule check error: {e}[/red]")
        _log.exception("check-schedule command failed")


@cli.command()
def daily_post():
    """
    Run daily automated social media posting.

    Posts one random painting to all configured platforms.
    Uses rounds logic to ensure all paintings are posted before repeating.
    Designed to be called by cron job at 8:30 AM daily.

    Example:
        python main.py daily-post
    """
    from src.app.social.daily_poster import run_daily_post
    from src.app.services.activity_log import log_activity
    from config.settings import METADATA_OUTPUT_PATH

    ui = CLIInterface()
    log_activity("CLI: daily-post")

    try:
        success = run_daily_post(METADATA_OUTPUT_PATH)
        if not success:
            ui.print_error("Daily post failed")
            import sys
            sys.exit(1)
    except KeyboardInterrupt:
        ui.print_warning("\nDaily posting interrupted by user")
    except Exception as e:
        ui.print_error(f"Error: {e}")
        _log.exception("daily-post command failed")
        sys.exit(1)


if __name__ == '__main__':
    cli()
