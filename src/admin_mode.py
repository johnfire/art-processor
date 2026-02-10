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
            self.show_main_menu()
            choice = IntPrompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "6", "7", "0"],
                default="0"
            )
            
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
        from src.upload_tracker import UploadTracker
        
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
        from src.collection_folder_manager import sync_collection_folders_cli
        
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
        
        input("\nPress Enter to continue...")

        
        Prompt.ask("\nPress Enter to continue")
