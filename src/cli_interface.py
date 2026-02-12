"""
Interactive CLI interface for user input.
Uses rich library for beautiful terminal output.
"""

from typing import Optional, List
from datetime import datetime

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.table import Table
from rich.panel import Panel

from config.settings import (
    MEDIUMS,
    SUBSTRATES,
    SUBJECTS,
    STYLES,
    COLLECTIONS,
    DIMENSION_UNIT,
)


console = Console()


class CLIInterface:
    """Handles interactive command-line interface."""
    
    def __init__(self):
        """Initialize CLI interface."""
        self.console = console
    
    def print_header(self, text: str):
        """Print a styled header."""
        self.console.print(f"\n[bold cyan]{text}[/bold cyan]")
        self.console.print("=" * len(text))
    
    def print_success(self, text: str):
        """Print success message."""
        self.console.print(f"[green]✓[/green] {text}")
    
    def print_warning(self, text: str):
        """Print warning message."""
        self.console.print(f"[yellow]⚠[/yellow] {text}")
    
    def print_error(self, text: str):
        """Print error message."""
        self.console.print(f"[red]✗[/red] {text}")
    
    def print_info(self, text: str):
        """Print info message."""
        self.console.print(f"[blue]→[/blue] {text}")
    
    
    def select_title(self, titles: List[str]) -> int:
        """
        Let user select a title from generated options.

        Args:
            titles: List of title options

        Returns:
            Index of selected title
        """
        self.print_header("Generated Title Options")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column("Title")
        
        for i, title in enumerate(titles, 1):
            table.add_row(str(i), title)
        
        self.console.print(table)
        
        choice = IntPrompt.ask(
            "\nSelect title number",
            default=1,
            choices=[str(i) for i in range(1, len(titles) + 1)],
        )

        return choice - 1
    
    def ask_for_user_title(self) -> tuple:
        """
        Ask if user has their own title or wants AI to generate.

        Returns:
            Tuple of (has_own_title: bool, title: str or None)
        """
        self.print_header("Painting Title")

        has_own = Confirm.ask(
            "Do you have a name for this painting?",
            default=False
        )

        if has_own:
            title = Prompt.ask("Enter your title for this painting")
            return True, title
        else:
            return False, None

    def select_or_custom_title(self, ai_titles: List[str]) -> tuple:
        """
        Display AI-generated titles and let user choose one or enter custom title.

        Args:
            ai_titles: List of AI-generated title options

        Returns:
            Tuple of (selected_title: str, all_titles: List[str])
        """
        self.print_header("AI-Generated Title Options")

        # Display AI titles in a table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column("Title")

        for i, title in enumerate(ai_titles, 1):
            table.add_row(str(i), title)

        self.console.print(table)

        # Ask if user wants to use AI title or enter custom
        use_ai = Confirm.ask(
            "\nUse one of the AI-generated titles?",
            default=True
        )

        if use_ai:
            # User wants to select an AI title
            choice = IntPrompt.ask(
                "Select title number",
                default=1,
                choices=[str(i) for i in range(1, len(ai_titles) + 1)],
            )
            selected_title = ai_titles[choice - 1]
            return selected_title, ai_titles
        else:
            # User wants to enter custom title
            custom_title = Prompt.ask("Enter your custom title for this painting")
            return custom_title, [custom_title]

    def input_painting_notes(self) -> Optional[str]:
        """
        Get optional multi-line notes from user about the painting.

        Returns:
            User notes as a string, or None if skipped
        """
        self.print_header("Painting Notes (Optional)")
        self.console.print("[dim]Enter your notes about the painting to help AI generate a better description.[/dim]")
        self.console.print("[dim]Press Enter on an empty line to finish, or just Enter to skip.[/dim]\n")

        lines = []
        first_line = True

        while True:
            try:
                if first_line:
                    line = input()
                    first_line = False
                    # If first line is empty, user is skipping
                    if not line.strip():
                        return None
                    lines.append(line)
                else:
                    line = input()
                    # Empty line signals end of input
                    if not line.strip():
                        break
                    lines.append(line)
            except EOFError:
                break

        notes = "\n".join(lines).strip()
        return notes if notes else None

    def select_substrate(self) -> str:
        """
        Let user select substrate from predefined options.
        
        Returns:
            Selected substrate
        """
        self.print_header("Select Substrate")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column("Substrate")
        
        for i, substrate in enumerate(SUBSTRATES, 1):
            table.add_row(str(i), substrate)
        
        self.console.print(table)
        
        choice = IntPrompt.ask(
            "\nSelect substrate number",
            default=1,
            choices=[str(i) for i in range(1, len(SUBSTRATES) + 1)],
        )
        
        return SUBSTRATES[choice - 1]
    
    def select_medium(self) -> str:
        """
        Let user select medium from predefined options.
        
        Returns:
            Selected medium
        """
        self.print_header("Select Medium")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column("Medium")
        
        for i, medium in enumerate(MEDIUMS, 1):
            table.add_row(str(i), medium)
        
        self.console.print(table)
        
        choice = IntPrompt.ask(
            "\nSelect medium number",
            default=1,
            choices=[str(i) for i in range(1, len(MEDIUMS) + 1)],
        )
        
        return MEDIUMS[choice - 1]
    
    def select_subject(self) -> str:
        """
        Let user select subject from predefined options.
        
        Returns:
            Selected subject
        """
        self.print_header("Select Subject")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column("Subject")
        
        for i, subject in enumerate(SUBJECTS, 1):
            table.add_row(str(i), subject)
        
        self.console.print(table)
        
        choice = IntPrompt.ask(
            "\nSelect subject number",
            default=1,
            choices=[str(i) for i in range(1, len(SUBJECTS) + 1)],
        )
        
        return SUBJECTS[choice - 1]
    
    def select_style(self) -> str:
        """
        Let user select style from predefined options.
        
        Returns:
            Selected style
        """
        self.print_header("Select Style")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column("Style")
        
        for i, style in enumerate(STYLES, 1):
            table.add_row(str(i), style)
        
        self.console.print(table)
        
        choice = IntPrompt.ask(
            "\nSelect style number",
            default=1,
            choices=[str(i) for i in range(1, len(STYLES) + 1)],
        )
        
        return STYLES[choice - 1]
    
    def select_collection(self) -> str:
        """
        Let user select collection from predefined options.
        
        Returns:
            Selected collection
        """
        self.print_header("Select Collection")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column("Collection")
        
        for i, collection in enumerate(COLLECTIONS, 1):
            table.add_row(str(i), collection)
        
        self.console.print(table)
        
        choice = IntPrompt.ask(
            "\nSelect collection number",
            default=1,
            choices=[str(i) for i in range(1, len(COLLECTIONS) + 1)],
        )
        
        return COLLECTIONS[choice - 1]
    
    def input_price(self, default: float = 0.0) -> float:
        """
        Get price input from user.
        
        Args:
            default: Default price value
            
        Returns:
            Price in euros
        """
        return FloatPrompt.ask(
            "Enter price (EUR)",
            default=default,
        )
    
    def input_dimensions(self, unit: str = "cm") -> tuple:
        """
        Get width, height, and depth from user.
        
        Args:
            unit: Unit of measurement ("cm" or "in")
            
        Returns:
            Tuple of (width, height, depth, formatted_string)
        """
        from rich.prompt import FloatPrompt
        
        self.print_header(f"Enter Dimensions ({unit})")
        
        width = FloatPrompt.ask(f"Width ({unit})", default=0.0)
        height = FloatPrompt.ask(f"Height ({unit})", default=0.0)
        depth = FloatPrompt.ask(f"Depth ({unit}) - enter 0 for flat works", default=0.0)
        
        # Format the dimension string
        if depth > 0:
            formatted = f"{width}{unit} x {height}{unit} x {depth}{unit}"
        else:
            formatted = f"{width}{unit} x {height}{unit}"
            depth = None  # Set to None for flat works
        
        return width, height, depth, formatted
    
    def input_creation_date(self, suggested_date: str) -> str:
        """
        Get creation date from user.
        
        Args:
            suggested_date: Suggested date from EXIF/file
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        self.console.print(f"\n[dim]Suggested date from EXIF: {suggested_date}[/dim]")
        
        date_input = Prompt.ask(
            "Enter creation date (YYYY-MM-DD) or press Enter to accept suggested",
            default=suggested_date,
        )
        
        return date_input
    
    def confirm_processing(self, filename: str) -> bool:
        """
        Ask for confirmation before processing.
        
        Args:
            filename: Name of file to process
            
        Returns:
            True if user confirms
        """
        return Confirm.ask(f"\nProcess {filename}?", default=True)
    
    def show_processing_summary(self, metadata: dict):
        """
        Display summary of processed artwork.
        
        Args:
            metadata: Metadata dictionary
        """
        self.console.print("\n")
        panel_content = f"""[bold]{metadata['title']['selected']}[/bold]

[dim]Category:[/dim] {metadata['category']}
[dim]Medium:[/dim] {metadata['medium']}
[dim]Dimensions:[/dim] {metadata['dimensions']}
[dim]Price:[/dim] €{metadata['price_eur']}
[dim]Date:[/dim] {metadata['creation_date']}

[dim]Description:[/dim]
{metadata['description']}
"""
        
        panel = Panel(
            panel_content,
            title="Processing Complete",
            border_style="green",
        )
        
        self.console.print(panel)
    
    def show_file_info(self, big_file, instagram_file):
        """
        Display information about file pair.
        
        Args:
            big_file: Path to big version
            instagram_file: Path to instagram version or None
        """
        self.console.print(f"\n[bold]File:[/bold] {big_file.name}")
        self.console.print(f"[dim]Big version:[/dim] {big_file}")
        
        if instagram_file:
            self.console.print(f"[dim]Instagram version:[/dim] {instagram_file}")
        else:
            self.console.print(f"[yellow]Instagram version: Not found[/yellow]")
