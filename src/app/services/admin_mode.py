"""
Admin mode for managing configuration settings.
Allows editing settings.py through interactive CLI.
"""

import re
from pathlib import Path
from typing import List

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel

from src.app.services.activity_log import log_admin_action

console = Console()


class AdminMode:
    """Handles administrative configuration management."""
    
    def __init__(self, settings_path: Path):
        """Initialize admin mode with path to settings.py."""
        self.settings_path = settings_path
        self.console = console
    
    def run(self):
        """Run the admin mode menu loop."""
        while True:
            self._show_login_alerts()
            self.show_main_menu()
            choice = IntPrompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "0"],
                default="0"
            )

            if choice != 0:
                log_admin_action(choice)

            if choice == 0:
                self.console.print("\n[green]Exiting admin mode[/green]")
                break
            elif choice == 1:
                self.edit_api_key()
            elif choice == 2:
                self.edit_file_paths()
            elif choice == 3:
                self.edit_dimension_unit()
            elif choice == 4:
                self.add_to_list()
            elif choice == 5:
                self.manage_social_platforms()
            elif choice == 6:
                self.sync_collection_folders()
            elif choice == 7:
                self.view_current_settings()
            elif choice == 8:
                self.generate_skeleton_metadata()
            elif choice == 9:
                self.edit_metadata()
            elif choice == 10:
                self.sync_instagram_folders()
            elif choice == 11:
                self.upload_to_faso()
            elif choice == 12:
                self.find_painting()
            elif choice == 13:
                self.post_to_social_media()
            elif choice == 14:
                self.schedule_posts()
            elif choice == 15:
                self.view_schedule()
            elif choice == 16:
                self.migrate_tracking()
            elif choice == 17:
                self.manual_site_login()
    
    def show_main_menu(self):
        """Display the main admin menu."""
        self.console.print("\n[bold cyan]═══ ADMIN MODE ═══[/bold cyan]\n")
        
        table = Table(show_header=False)
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Description")
        
        table.add_row("1", "Edit Anthropic API Key")
        table.add_row("2", "Edit File Paths")
        table.add_row("3", "Edit Dimension Unit (cm/in)")
        table.add_row("4", "Add to Lists (Substrates, Mediums, etc.)")
        table.add_row("5", "Manage Social Media Platforms")
        table.add_row("6", "Sync Collection Folders")
        table.add_row("7", "View Current Settings")
        table.add_row("8", "Generate Skeleton Metadata")
        table.add_row("9", "Edit Metadata")
        table.add_row("10", "Sync Instagram Folders")
        table.add_row("11", "Upload to FASO")
        table.add_row("12", "Find Painting")
        table.add_row("13", "Post to Social Media")
        table.add_row("14", "Schedule Posts")
        table.add_row("15", "View Schedule")
        table.add_row("16", "Migrate Tracking Data")
        table.add_row("17", "Manual Site Login (Cara / FASO)")
        table.add_row("0", "Exit Admin Mode")
        
        self.console.print(table)
    
    def edit_api_key(self):
        """Edit the Anthropic API key in .env file."""
        self.console.print("\n[bold]Edit Anthropic API Key[/bold]")
        
        # Get parent directory to find .env
        env_path = self.settings_path.parent.parent / ".env"
        
        if not env_path.exists():
            self.console.print(f"[yellow]Warning: .env file not found at {env_path}[/yellow]")
            create = Confirm.ask("Create .env file?")
            if not create:
                return
            env_path.touch()
        
        # Read current .env
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Find existing API key line
        api_key_line_idx = None
        current_key = None
        for i, line in enumerate(lines):
            if line.startswith('ANTHROPIC_API_KEY='):
                api_key_line_idx = i
                current_key = line.split('=', 1)[1].strip()
                break
        
        if current_key:
            masked = current_key[:8] + "..." if len(current_key) > 8 else "***"
            self.console.print(f"[dim]Current key: {masked}[/dim]")
        
        new_key = Prompt.ask("Enter new API key (or press Enter to keep current)", default="")
        
        if new_key:
            new_line = f"ANTHROPIC_API_KEY={new_key}\n"
            if api_key_line_idx is not None:
                lines[api_key_line_idx] = new_line
            else:
                lines.append(new_line)
            
            with open(env_path, 'w') as f:
                f.writelines(lines)
            
            self.console.print("[green]✓ API key updated[/green]")
        else:
            self.console.print("[yellow]No changes made[/yellow]")
    
    def edit_file_paths(self):
        """Edit file paths in .env file."""
        self.console.print("\n[bold]Edit File Paths[/bold]")
        
        env_path = self.settings_path.parent.parent / ".env"
        
        if not env_path.exists():
            self.console.print(f"[red].env file not found at {env_path}[/red]")
            return
        
        # Read current .env
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Path variables to edit
        path_vars = {
            'PAINTINGS_BIG_PATH': 'Big paintings folder',
            'PAINTINGS_INSTAGRAM_PATH': 'Instagram paintings folder',
            'METADATA_OUTPUT_PATH': 'Metadata output folder',
        }
        
        changes_made = False
        
        for var_name, description in path_vars.items():
            # Find current value
            current_value = None
            var_line_idx = None
            
            for i, line in enumerate(lines):
                if line.startswith(f'{var_name}='):
                    var_line_idx = i
                    current_value = line.split('=', 1)[1].strip()
                    break
            
            self.console.print(f"\n[cyan]{description}[/cyan]")
            if current_value:
                self.console.print(f"[dim]Current: {current_value}[/dim]")
            
            new_value = Prompt.ask("Enter new path (or press Enter to keep current)", default="")
            
            if new_value:
                new_line = f"{var_name}={new_value}\n"
                if var_line_idx is not None:
                    lines[var_line_idx] = new_line
                else:
                    lines.append(new_line)
                changes_made = True
        
        if changes_made:
            with open(env_path, 'w') as f:
                f.writelines(lines)
            self.console.print("\n[green]✓ File paths updated[/green]")
        else:
            self.console.print("\n[yellow]No changes made[/yellow]")
    
    def edit_dimension_unit(self):
        """Edit the dimension unit setting."""
        self.console.print("\n[bold]Edit Dimension Unit[/bold]")
        
        # Read settings file
        with open(self.settings_path, 'r') as f:
            content = f.read()
        
        # Find current unit
        match = re.search(r'DIMENSION_UNIT\s*=\s*"(\w+)"', content)
        current_unit = match.group(1) if match else "cm"
        
        self.console.print(f"[dim]Current unit: {current_unit}[/dim]")
        
        choice = IntPrompt.ask(
            "\n1. Centimeters (cm)\n2. Inches (in)\n\nSelect unit",
            choices=["1", "2"],
            default="1" if current_unit == "cm" else "2"
        )
        
        new_unit = "cm" if choice == 1 else "in"
        
        # Replace in file
        new_content = re.sub(
            r'DIMENSION_UNIT\s*=\s*"(\w+)"',
            f'DIMENSION_UNIT = "{new_unit}"',
            content
        )
        
        with open(self.settings_path, 'w') as f:
            f.write(new_content)
        
        self.console.print(f"[green]✓ Dimension unit set to: {new_unit}[/green]")
    
    def add_to_list(self):
        """Add new entries to configuration lists."""
        self.console.print("\n[bold]Add to Configuration Lists[/bold]")
        
        lists = {
            "1": ("SUBSTRATES", "Substrate"),
            "2": ("MEDIUMS", "Medium"),
            "3": ("SUBJECTS", "Subject"),
            "4": ("STYLES", "Style"),
            "5": ("COLLECTIONS", "Collection"),
        }
        
        # Show menu
        table = Table(show_header=False)
        table.add_column("Option", style="cyan", width=8)
        table.add_column("List")
        
        for key, (var_name, display_name) in lists.items():
            table.add_row(key, display_name + "s")
        table.add_row("0", "Back to main menu")
        
        self.console.print(table)
        
        choice = Prompt.ask("\nSelect list to add to", choices=list(lists.keys()) + ["0"])
        
        if choice == "0":
            return
        
        var_name, display_name = lists[choice]
        
        # Get new entry
        new_entry = Prompt.ask(f"\nEnter new {display_name.lower()}")
        
        if not new_entry:
            self.console.print("[yellow]No entry provided[/yellow]")
            return
        
        # Read settings file
        with open(self.settings_path, 'r') as f:
            content = f.read()
        
        # Find the list and add entry
        # Pattern: LISTNAME = [\n    "item1",\n    "item2",\n]
        pattern = f'{var_name}\\s*=\\s*\\[(.*?)\\]'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            list_content = match.group(1)
            # Add new entry before the closing bracket
            new_list_content = list_content.rstrip() + f'\n    "{new_entry}",\n'
            new_content = content.replace(match.group(0), f'{var_name} = [{new_list_content}]')
            
            with open(self.settings_path, 'w') as f:
                f.write(new_content)
            
            self.console.print(f'[green]✓ Added "{new_entry}" to {display_name}s[/green]')
        else:
            self.console.print(f"[red]Could not find {var_name} list in settings[/red]")
    
    def manage_social_platforms(self):
        """Manage social media platforms for upload tracking."""
        from pathlib import Path
        from src.app.services.upload_tracker import UploadTracker
        
        self.console.print("\n[bold]Manage Social Media Platforms[/bold]")
        
        # Get tracker file path
        tracker_path = self.settings_path.parent.parent / "upload_status.json"
        tracker = UploadTracker(tracker_path)
        
        # Show current platforms
        platforms = tracker.get_platforms()
        
        self.console.print("\n[cyan]Current Platforms:[/cyan]")
        for i, platform in enumerate(platforms, 1):
            self.console.print(f"  {i}. {platform}")
        
        # Ask to add new platform
        add_new = Confirm.ask("\nAdd a new platform?", default=True)
        
        if add_new:
            platform_name = Prompt.ask("Enter platform name (e.g., Instagram, Mastodon, TikTok)")
            
            if platform_name:
                tracker.add_platform(platform_name)
                self.console.print(f"[green]✓ Added platform: {platform_name}[/green]")
            else:
                self.console.print("[yellow]No platform added[/yellow]")
    
    def view_current_settings(self):
        """Display current configuration settings."""
        self.console.print("\n[bold cyan]Current Settings[/bold cyan]\n")
        
        # Read .env
        env_path = self.settings_path.parent.parent / ".env"
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Extract key settings
            api_key = None
            for line in env_content.split('\n'):
                if line.startswith('ANTHROPIC_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    api_key = key[:8] + "..." if len(key) > 8 else "***"
            
            if api_key:
                self.console.print(f"[cyan]API Key:[/cyan] {api_key}")
        
        # Read settings.py
        with open(self.settings_path, 'r') as f:
            content = f.read()
        
        # Extract dimension unit
        match = re.search(r'DIMENSION_UNIT\s*=\s*"(\w+)"', content)
        if match:
            self.console.print(f"[cyan]Dimension Unit:[/cyan] {match.group(1)}")
        
        # Show list counts
        lists = {
            "SUBSTRATES": "Substrates",
            "MEDIUMS": "Mediums",
            "SUBJECTS": "Subjects",
            "STYLES": "Styles",
            "COLLECTIONS": "Collections",
        }
        
        self.console.print("\n[bold]List Sizes:[/bold]")
        for var_name, display_name in lists.items():
            pattern = f'{var_name}\\s*=\\s*\\[(.*?)\\]'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                # Count items (rough count by counting quotes)
                count = match.group(1).count('"') // 2
                self.console.print(f"  {display_name}: {count} entries")
    
    def sync_collection_folders(self):
        """Sync collection folders - create any missing folders."""
        from src.app.services.collection_folder_manager import sync_collection_folders_cli
        
        self.console.print("\n[bold]Sync Collection Folders[/bold]")
        self.console.print("[dim]Creates folders for any collections that don't exist yet[/dim]\n")
        
        if not Confirm.ask("Proceed with sync?", default=True):
            return
        
        # Run the sync
        result = sync_collection_folders_cli()
        
        # Show results
        self.console.print(f"\n[bold]Results:[/bold]")
        self.console.print(f"Total collections: {result['total_collections']}")
        self.console.print(f"Folders created: {result['missing_count']}")
        
        if result['errors']:
            self.console.print(f"[red]Errors: {len(result['errors'])}[/red]")
        
        Prompt.ask("\nPress Enter to continue")

    def generate_skeleton_metadata(self):
        """Generate skeleton metadata files for all painting folders."""
        from src.app.services.skeleton_metadata_generator import generate_skeleton_metadata_cli

        self.console.print("\n[bold]Generate Skeleton Metadata[/bold]")
        self.console.print(
            "[dim]Scans painting folders and creates stub metadata files[/dim]\n"
        )

        if not Confirm.ask("Proceed with scan?", default=True):
            return

        generate_skeleton_metadata_cli()

        Prompt.ask("\nPress Enter to continue")

    def edit_metadata(self):
        """Edit metadata files interactively."""
        from src.app.services.metadata_editor import edit_metadata_cli

        self.console.print("\n[bold]Edit Metadata[/bold]")
        self.console.print(
            "[dim]Browse and edit metadata files in processed-metadata[/dim]\n"
        )

        edit_metadata_cli()

        Prompt.ask("\nPress Enter to continue")

    def sync_instagram_folders(self):
        """Sync instagram folder structure to match big paintings."""
        from src.app.services.instagram_folder_sync import sync_instagram_folders_cli

        self.console.print("\n[bold]Sync Instagram Folders[/bold]")
        self.console.print(
            "[dim]Reorganize instagram photos to match big folder structure[/dim]\n"
        )

        sync_instagram_folders_cli()

        Prompt.ask("\nPress Enter to continue")

    def upload_to_faso(self):
        """Upload artwork to FASO website."""
        from src.app.galleries.faso_uploader import upload_faso_cli

        self.console.print("\n[bold]Upload to FASO[/bold]")
        self.console.print(
            "[dim]Upload paintings to Fine Art Studio Online[/dim]\n"
        )

        upload_faso_cli()

        Prompt.ask("\nPress Enter to continue")

    def find_painting(self):
        """Find a painting by name across paintings directories."""
        from config.settings import PAINTINGS_BIG_PATH, PAINTINGS_INSTAGRAM_PATH

        self.console.print("\n[bold]Find Painting[/bold]")
        self.console.print(
            "[dim]Search for a painting by name in paintings folders[/dim]\n"
        )

        query = Prompt.ask("Painting name")
        if not query.strip():
            return

        # Normalize query: lowercase, replace separators with spaces, strip trailing numbers
        normalized_query = self._normalize_painting_name(query)

        results = []
        search_dirs = [
            ("paintings-big", PAINTINGS_BIG_PATH),
            ("paintings-instagram", PAINTINGS_INSTAGRAM_PATH),
        ]

        for label, base_path in search_dirs:
            if not base_path.exists():
                continue
            for filepath in base_path.rglob("*"):
                if not filepath.is_file():
                    continue
                normalized_file = self._normalize_painting_name(filepath.stem)
                if normalized_query in normalized_file:
                    results.append((label, filepath))

        if not results:
            self.console.print(f"[yellow]No matches found for '{query}'[/yellow]")
        else:
            table = Table(title=f"Results for '{query}'")
            table.add_column("Location", style="cyan")
            table.add_column("Path")

            for label, filepath in sorted(results, key=lambda r: r[1].name):
                table.add_row(label, str(filepath))

            self.console.print(table)
            self.console.print(f"\n[dim]{len(results)} file(s) found[/dim]")

        Prompt.ask("\nPress Enter to continue")

    def post_to_social_media(self):
        """Post artwork to social media platforms."""
        from src.app.social.cli import post_social_cli

        self.console.print("\n[bold]Post to Social Media[/bold]")
        self.console.print("[dim]Post artwork to your social media accounts[/dim]\n")

        post_social_cli()

        Prompt.ask("\nPress Enter to continue")

    def schedule_posts(self):
        """Schedule future social media posts."""
        from src.app.social.cli import schedule_post_cli

        self.console.print("\n[bold]Schedule Posts[/bold]")
        self.console.print("[dim]Schedule artwork posts for specific dates and times[/dim]\n")

        schedule_post_cli()

        Prompt.ask("\nPress Enter to continue")

    def view_schedule(self):
        """View upcoming and past scheduled posts."""
        from src.app.social.cli import view_schedule_cli

        self.console.print("\n[bold]Post Schedule[/bold]")
        self.console.print("[dim]View upcoming and past scheduled posts[/dim]\n")

        view_schedule_cli()

        Prompt.ask("\nPress Enter to continue")

    def migrate_tracking(self):
        """Migrate upload_status.json to metadata-based tracking."""
        from src.app.services.migrate_tracking import migrate

        self.console.print("\n[bold]Migrate Tracking Data[/bold]")
        self.console.print(
            "[dim]Moves upload tracking from upload_status.json into each painting's metadata[/dim]\n"
        )

        if not Confirm.ask("Run migration?", default=True):
            return

        migrate()

        Prompt.ask("\nPress Enter to continue")

    def _show_login_alerts(self):
        """Display login expiry warnings for browser-session platforms."""
        from config.settings import LOGIN_STATUS_PATH
        from src.app.services.login_tracker import LoginTracker

        tracker = LoginTracker(LOGIN_STATUS_PATH)
        alerts = tracker.get_alerts()
        if not alerts:
            return

        self.console.print()
        for platform, status in alerts:
            label = platform.upper()
            if status["status"] == "never":
                self.console.print(
                    f"[bold red]LOGIN ALERT: {label} — never logged in. Use option 17.[/bold red]"
                )
            elif status["status"] == "expired":
                self.console.print(
                    f"[bold red]LOGIN ALERT: {label} — login expired "
                    f"({status['days_since']} days ago). Use option 17.[/bold red]"
                )
            elif status["status"] == "warn":
                self.console.print(
                    f"[yellow]LOGIN WARNING: {label} — login expires in "
                    f"{status['days_remaining']} day(s). Use option 17 soon.[/yellow]"
                )

    def manual_site_login(self):
        """Run manual browser login for Cara or FASO and record the timestamp."""
        from config.settings import LOGIN_STATUS_PATH
        from src.app.services.login_tracker import LoginTracker

        self.console.print("\n[bold]Manual Site Login[/bold]")
        self.console.print("[dim]Opens a browser so you can log in manually. Session is saved.[/dim]\n")

        table = Table(show_header=False)
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Site")
        table.add_row("1", "FASO (Fine Art Studio Online)")
        table.add_row("2", "Cara")
        table.add_row("0", "Back")
        self.console.print(table)

        choice = Prompt.ask("\nSelect site", choices=["1", "2", "0"], default="0")
        if choice == "0":
            return

        tracker = LoginTracker(LOGIN_STATUS_PATH)

        if choice == "1":
            import asyncio
            from manual_login import manual_login_and_save
            try:
                asyncio.run(manual_login_and_save())
                tracker.record_login("faso")
                self.console.print("[green]FASO login recorded.[/green]")
            except KeyboardInterrupt:
                self.console.print("[yellow]Login cancelled.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        elif choice == "2":
            from src.app.social.cara import CaraPlatform
            try:
                CaraPlatform().setup_session()
                tracker.record_login("cara")
                self.console.print("[green]Cara login recorded.[/green]")
            except KeyboardInterrupt:
                self.console.print("[yellow]Login cancelled.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        Prompt.ask("\nPress Enter to continue")

    @staticmethod
    def _normalize_painting_name(name: str) -> str:
        """Normalize a painting name for fuzzy searching.
        Strips trailing numbers, replaces dashes/underscores with spaces, lowercases.
        """
        # Remove file extension if present
        name = Path(name).stem if '.' in name else name
        # Lowercase
        name = name.lower()
        # Replace dashes and underscores with spaces
        name = name.replace('-', ' ').replace('_', ' ')
        # Strip trailing numbers (e.g., "black palm 1" -> "black palm")
        name = re.sub(r'\s+\d+\s*$', '', name)
        # Also strip trailing letter+number combos like A4, A14
        name = re.sub(r'\s+[a-z]\d+\s*$', '', name)
        # Collapse whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        return name
