"""
Manual login helper - Login yourself using a persistent browser profile.
All browser state (cookies, localStorage, sessions) is saved automatically.
"""

import asyncio
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright
from rich.console import Console

from config.settings import COOKIES_DIR

console = Console()

# Persistent browser profile directory
BROWSER_PROFILE_DIR = COOKIES_DIR / "faso_browser_profile"


async def manual_login_and_save():
    """
    Opens a persistent browser profile, lets you login manually.
    All state is saved automatically to disk.
    """
    console.print("\n[bold cyan]═══ FASO Manual Login Helper ═══[/bold cyan]\n")
    console.print("[yellow]This will:[/yellow]")
    console.print("[yellow]1. Open a browser with a saved profile[/yellow]")
    console.print("[yellow]2. Let YOU login manually (solve CAPTCHA, etc.)[/yellow]")
    console.print("[yellow]3. Automatically save all session data[/yellow]")
    console.print("[yellow]4. Future runs will reuse this profile (no login needed!)[/yellow]\n")

    # Create profile directory
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    input("Press Enter to open browser...")

    async with async_playwright() as p:
        # Use persistent context - saves ALL browser state to disk
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE_DIR),
            headless=False,
            viewport={'width': 1920, 'height': 1080},
            args=[
                '--disable-blink-features=AutomationControlled',
            ],
        )

        # Hide automation markers
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        page = context.pages[0] if context.pages else await context.new_page()

        # Go to FASO login page directly
        console.print("[cyan]Opening FASO login...[/cyan]")
        await page.goto('https://data.fineartstudioonline.com/login/')
        await page.wait_for_load_state('networkidle')

        current_url = page.url
        console.print(f"[cyan]Current URL: {current_url}[/cyan]")

        if '/login' in current_url.lower():
            console.print("\n[bold green]═══ NOW IT'S YOUR TURN! ═══[/bold green]")
            console.print("[green]1. Login manually in the browser[/green]")
            console.print("[green]2. Solve any CAPTCHA that appears[/green]")
            console.print("[green]3. Wait until you see your dashboard/home page[/green]")
            console.print("[green]4. Come back here and press Enter[/green]\n")
        else:
            console.print("[green]Already logged in from previous session![/green]")

        input("Press Enter when you're done (session saves automatically)...")

        console.print(f"[cyan]Final URL: {page.url}[/cyan]")

        # Verify session by navigating to the admin dashboard
        console.print("\n[cyan]Verifying session - navigating to dashboard...[/cyan]")
        await page.goto('https://data.fineartstudioonline.com/')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        final_url = page.url
        console.print(f"[cyan]Dashboard URL: {final_url}[/cyan]")

        # Check if we're on the admin backend (not redirected to public site)
        if urlparse(final_url).hostname == 'data.fineartstudioonline.com' and '/login' not in final_url.lower():
            console.print("[bold green]Session verified! Dashboard accessible.[/bold green]")
            marker = BROWSER_PROFILE_DIR / ".logged_in"
            marker.write_text("ok")
        elif '/login' in final_url.lower():
            console.print("[bold red]Login did not persist. Try again:[/bold red]")
            console.print("[yellow]1. Login in the browser again[/yellow]")
            console.print("[yellow]2. After seeing the dashboard, press Enter here[/yellow]")
            input("Press Enter to retry verification...")
            await page.goto('https://data.fineartstudioonline.com/')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            final_url = page.url
            console.print(f"[cyan]Retry URL: {final_url}[/cyan]")
            marker = BROWSER_PROFILE_DIR / ".logged_in"
            marker.write_text("ok")
        else:
            # Redirected to faso.com or elsewhere
            console.print(f"[yellow]Redirected to: {final_url}[/yellow]")
            console.print("[yellow]Session may have saved. Marking profile as ready.[/yellow]")
            marker = BROWSER_PROFILE_DIR / ".logged_in"
            marker.write_text("ok")

        await context.close()

    console.print(f"\n[bold green]Session saved to: {BROWSER_PROFILE_DIR}[/bold green]")
    console.print("[cyan]All future automation will reuse this browser profile.[/cyan]\n")


if __name__ == "__main__":
    try:
        asyncio.run(manual_login_and_save())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
