"""
Manual login helper - Login yourself, save cookies for automation.
"""

import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright
from rich.console import Console

console = Console()


async def manual_login_and_save_cookies():
    """
    Opens browser, lets you login manually, saves cookies.
    """
    console.print("\n[bold cyan]═══ FASO Manual Login Helper ═══[/bold cyan]\n")
    console.print("[yellow]This will:[/yellow]")
    console.print("[yellow]1. Open a browser[/yellow]")
    console.print("[yellow]2. Let YOU login manually (solve CAPTCHA, etc.)[/yellow]")
    console.print("[yellow]3. Save your session cookies[/yellow]")
    console.print("[yellow]4. Future automation will use these cookies (no login needed!)[/yellow]\n")
    
    input("Press Enter to open browser...")
    
    async with async_playwright() as p:
        # Launch browser in NON-headless mode
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100,
            args=[
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
        )
        
        # Hide automation markers
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        
        # Go to FASO login
        console.print("[cyan]Opening FASO login page...[/cyan]")
        await page.goto('https://data.fineartstudioonline.com/login/')
        
        console.print("\n[bold green]═══ NOW IT'S YOUR TURN! ═══[/bold green]")
        console.print("[green]1. Login manually in the browser[/green]")
        console.print("[green]2. Solve any CAPTCHA that appears[/green]")
        console.print("[green]3. Wait until you see your dashboard/home page[/green]")
        console.print("[green]4. Come back here and press Enter[/green]\n")
        
        input("Press Enter AFTER you've successfully logged in...")
        
        # Check if actually logged in
        current_url = page.url
        
        if 'login' in current_url.lower():
            console.print("[red]✗ Still on login page. Login may have failed.[/red]")
            console.print("[yellow]Try again and make sure you're fully logged in.[/yellow]")
            await browser.close()
            return False
        
        console.print(f"[green]✓ Logged in! Current URL: {current_url}[/green]")
        
        # Save cookies
        cookies = await context.cookies()
        
        from config.settings import FASO_COOKIES_PATH
        cookies_file = FASO_COOKIES_PATH
        
        import json
        with open(cookies_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        console.print(f"\n[bold green]✓ Success! Cookies saved to {cookies_file}[/bold green]")
        console.print("[cyan]Future automation will use these cookies (no login needed!)[/cyan]\n")
        
        # Close browser
        await browser.close()
        
        return True


if __name__ == "__main__":
    success = asyncio.run(manual_login_and_save_cookies())
    
    if success:
        console.print("[bold green]All done! Now run your automation:[/bold green]")
        console.print("[cyan]python main.py test-faso-login[/cyan]\n")
