"""
FASO (Fine Art Studio Online) client for uploading artwork.
Handles authentication and navigation using Playwright.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from rich.console import Console

console = Console()


class FASOClient:
    """Client for interacting with FASO website."""
    
    def __init__(self, email: str, password: str, headless: bool = False, cookies_file: Path = None):
        """
        Initialize FASO client.
        
        Args:
            email: FASO account email
            password: FASO account password
            headless: Run browser in headless mode (default: False for debugging)
            cookies_file: Path to save/load cookies for session persistence
                         If None, uses FASO_COOKIES_PATH from settings
        """
        if cookies_file is None:
            from config.settings import FASO_COOKIES_PATH
            cookies_file = FASO_COOKIES_PATH
            
        self.email = email
        self.password = password
        self.headless = headless
        self.cookies_file = cookies_file
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def start(self):
        """Start the browser and create a new page."""
        console.print("[cyan]Starting browser...[/cyan]")
        
        self.playwright = await async_playwright().start()
        
        # Launch browser (chromium by default)
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=100,  # Slow down by 100ms to appear more human-like
            args=[
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
            ]
        )
        
        # Create browser context with anti-detection settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # NYC coords
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        
        # Add script to hide webdriver property (Cloudflare checks this)
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Hide Playwright
            delete window.playwright;
            
            // Make chrome object look real
            window.chrome = {
                runtime: {}
            };
            
            // Fake plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Fake languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        # Load cookies if they exist (skip login if already authenticated)
        if self.cookies_file.exists():
            console.print("[cyan]Loading saved session cookies...[/cyan]")
            import json
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
            console.print("[green]✓ Cookies loaded[/green]")
        
        # Create new page
        self.page = await self.context.new_page()
        
        console.print("[green]✓ Browser started[/green]")
    
    async def is_logged_in(self) -> bool:
        """
        Check if already logged in (useful when using saved cookies).
        
        Returns:
            True if logged in, False otherwise
        """
        if not self.page:
            return False
        
        try:
            # Navigate directly to the user dashboard (requires login)
            await self.page.goto(
                'https://data.fineartstudioonline.com/cfgeditwebsite.asp?new_login=y&faso_com_auth=y',
                timeout=10000,
            )
            await self.page.wait_for_load_state('networkidle', timeout=5000)

            # If redirected to login page, session has expired
            if 'login' in self.page.url.lower():
                return False

            return True

        except:
            return False
    
    async def login(self) -> bool:
        """
        Log into FASO website.
        Types slowly to avoid bot detection.
        
        Returns:
            True if login successful, False otherwise
        """
        if not self.page:
            console.print("[red]Error: Browser not started. Call start() first.[/red]")
            return False
        
        # Check if we're already logged in (from saved cookies)
        if self.cookies_file.exists():
            console.print("[cyan]Checking if saved session is still valid...[/cyan]")
            if await self.is_logged_in():
                console.print("[green]✓ Already logged in using saved session![/green]")
                return True
            else:
                console.print("[yellow]Saved session expired, logging in again...[/yellow]")
        
        try:
            console.print("[cyan]Navigating to FASO login page...[/cyan]")
            
            # Navigate to login page
            await self.page.goto('https://data.fineartstudioonline.com/login/')
            
            # Wait for page to load
            await self.page.wait_for_load_state('networkidle')
            
            # Add human-like delay before interacting
            await asyncio.sleep(2)
            
            console.print("[cyan]Entering credentials (typing slowly)...[/cyan]")
            
            # Type email slowly (human-like)
            # FASO uses name="Email" for the email field
            email_field = await self.page.wait_for_selector('input[name="Email"]')
            
            # Move mouse to field first (human-like)
            await email_field.hover()
            await asyncio.sleep(0.3)
            
            await email_field.click()
            await asyncio.sleep(0.5)
            
            # Type with random delays between 150-250ms
            for char in self.email:
                await email_field.type(char, delay=150 + (hash(char) % 100))
                
            # Small pause between fields
            await asyncio.sleep(1)
            
            # Type password slowly
            # FASO uses name="Password" for the password field
            password_field = await self.page.wait_for_selector('input[name="Password"]')
            
            # Move mouse to password field
            await password_field.hover()
            await asyncio.sleep(0.3)
            
            await password_field.click()
            await asyncio.sleep(0.5)
            
            # Type password with random delays
            for char in self.password:
                await password_field.type(char, delay=150 + (hash(char) % 100))
            
            # Small pause before submitting
            await asyncio.sleep(1)
            
            console.print("[cyan]Submitting login...[/cyan]")
            
            # Find and click submit button
            # Try multiple common selectors
            submit_button = None
            selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Sign in")',
                'button:has-text("Login")',
            ]
            
            for selector in selectors:
                try:
                    submit_button = await self.page.wait_for_selector(selector, timeout=2000)
                    if submit_button:
                        break
                except:
                    continue
            
            if not submit_button:
                console.print("[red]Error: Could not find submit button[/red]")
                return False
            
            await submit_button.click()
            
            # CAPTCHA appears AFTER submit - pause here!
            console.print("\n[bold yellow]═══ CAPTCHA CHECKPOINT ═══[/bold yellow]")
            console.print("[yellow]A 'Verify you are human' screen may appear now.[/yellow]")
            console.print("[yellow]If it does:[/yellow]")
            console.print("[yellow]  1. Click the checkbox[/yellow]")
            console.print("[yellow]  2. Wait for it to verify (checkmark appears)[/yellow]")
            console.print("[yellow]  3. Click it AGAIN if it asks you to[/yellow]")
            console.print("[cyan]Waiting 15 seconds for you to complete verification...[/cyan]\n")
            
            await asyncio.sleep(15)  # Long pause for manual CAPTCHA solving
            
            console.print("[green]Continuing...[/green]")
            
            # Wait for navigation after login
            console.print("[cyan]Waiting for login to complete...[/cyan]")
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check if login was successful
            # Look for signs of successful login (dashboard, menu, etc.)
            current_url = self.page.url
            
            if 'login' in current_url.lower():
                # Still on login page - probably failed
                console.print("[red]✗ Login failed - still on login page[/red]")
                
                # Check for error message
                try:
                    error = await self.page.wait_for_selector('.error, .alert-danger, [class*="error"]', timeout=2000)
                    if error:
                        error_text = await error.text_content()
                        console.print(f"[red]Error message: {error_text}[/red]")
                except:
                    pass
                
                return False
            
            console.print(f"[green]✓ Login successful! Current URL: {current_url}[/green]")

            # Navigate directly to the user dashboard
            console.print("[cyan]Navigating to user dashboard...[/cyan]")
            await self.page.goto(
                'https://data.fineartstudioonline.com/cfgeditwebsite.asp?new_login=y&faso_com_auth=y',
                timeout=10000,
            )
            await self.page.wait_for_load_state('networkidle')
            console.print(f"[green]✓ Dashboard loaded: {self.page.url}[/green]")

            # Save cookies for future sessions
            cookies = await self.context.cookies()
            import json
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            console.print(f"[green]✓ Session cookies saved to {self.cookies_file}[/green]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error during login: {e}[/red]")
            return False
    
    async def navigate_to_add_artwork(self) -> bool:
        """
        Navigate to the Add New Artwork page.
        
        Steps:
        1. Click "Works" in left menu
        2. Click "Add New Artwork" link
        
        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            console.print("[red]Error: Browser not started[/red]")
            return False
        
        try:
            console.print("[cyan]Looking for 'Works' in left menu...[/cyan]")
            
            # Wait for page to fully load
            await self.page.wait_for_load_state('networkidle')
            
            # Try to find and click "Works" button/link in left menu
            # Try multiple selectors
            works_selectors = [
                'a:has-text("Works")',
                'button:has-text("Works")',
                '[class*="menu"] a:has-text("Works")',
                '[class*="sidebar"] a:has-text("Works")',
                'nav a:has-text("Works")',
            ]
            
            works_button = None
            for selector in works_selectors:
                try:
                    works_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if works_button:
                        console.print(f"[green]✓ Found 'Works' button with selector: {selector}[/green]")
                        break
                except:
                    continue
            
            if not works_button:
                console.print("[red]✗ Could not find 'Works' button in menu[/red]")
                console.print(f"[yellow]Current URL: {self.page.url}[/yellow]")
                
                # Save screenshot for debugging
                from config.settings import SCREENSHOTS_DIR
                screenshot_path = SCREENSHOTS_DIR / "debug_after_login.png"
                await self.page.screenshot(path=str(screenshot_path))
                console.print(f"[yellow]Screenshot saved as {screenshot_path}[/yellow]")
                
                return False
            
            console.print("[cyan]Clicking 'Works'...[/cyan]")
            await works_button.click()
            
            # Wait for navigation
            await self.page.wait_for_load_state('networkidle')
            
            console.print(f"[green]✓ Navigated to Works page: {self.page.url}[/green]")
            
            # Now find "Add New Artwork" link
            console.print("[cyan]Looking for 'Add New Artwork' link...[/cyan]")
            
            add_artwork_selectors = [
                'a:has-text("Add New Artwork")',
                'button:has-text("Add New Artwork")',
                'a:has-text("Add Artwork")',
                '[href*="add"]',
            ]
            
            add_artwork_link = None
            for selector in add_artwork_selectors:
                try:
                    add_artwork_link = await self.page.wait_for_selector(selector, timeout=3000)
                    if add_artwork_link:
                        console.print(f"[green]✓ Found 'Add New Artwork' link with selector: {selector}[/green]")
                        break
                except:
                    continue
            
            if not add_artwork_link:
                console.print("[red]✗ Could not find 'Add New Artwork' link[/red]")
                console.print(f"[yellow]Current URL: {self.page.url}[/yellow]")
                
                # Save screenshot for debugging
                from config.settings import SCREENSHOTS_DIR
                screenshot_path = SCREENSHOTS_DIR / "debug_works_page.png"
                await self.page.screenshot(path=str(screenshot_path))
                console.print(f"[yellow]Screenshot saved as {screenshot_path}[/yellow]")
                
                return False
            
            console.print("[cyan]Clicking 'Add New Artwork'...[/cyan]")
            await add_artwork_link.click()
            
            # Wait for form to load
            await self.page.wait_for_load_state('networkidle')
            
            console.print(f"[green]✓ Successfully navigated to Add Artwork page![/green]")
            console.print(f"[green]Current URL: {self.page.url}[/green]")
            
            # Save screenshot of the form for reference
            from config.settings import SCREENSHOTS_DIR
            screenshot_path = SCREENSHOTS_DIR / "add_artwork_form.png"
            await self.page.screenshot(path=str(screenshot_path))
            console.print(f"[yellow]Screenshot saved as {screenshot_path}[/yellow]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error navigating to Add Artwork: {e}[/red]")
            
            # Save error screenshot
            if self.page:
                from config.settings import SCREENSHOTS_DIR
                screenshot_path = SCREENSHOTS_DIR / "debug_error.png"
                await self.page.screenshot(path=str(screenshot_path))
                console.print(f"[yellow]Error screenshot saved as {screenshot_path}[/yellow]")
            
            return False
    
    async def close(self):
        """Close the browser and cleanup."""
        console.print("[cyan]Closing browser...[/cyan]")
        
        if self.context:
            await self.context.close()
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        console.print("[green]✓ Browser closed[/green]")
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()


async def test_faso_login(email: str, password: str):
    """
    Test function to verify FASO login and navigation.
    
    Args:
        email: FASO email
        password: FASO password
    """
    async with FASOClient(email, password, headless=False) as client:
        # Step 1: Login
        if not await client.login():
            console.print("[red]Login failed. Stopping.[/red]")
            return False
        
        # Pause to let user see the page
        await asyncio.sleep(2)
        
        # Step 2: Navigate to Add Artwork
        if not await client.navigate_to_add_artwork():
            console.print("[red]Navigation failed. Stopping.[/red]")
            return False
        
        # Pause to let user see the form
        console.print("[cyan]Pausing for 10 seconds so you can see the form...[/cyan]")
        await asyncio.sleep(10)
        
        console.print("[green]✓ Test completed successfully![/green]")
        return True


if __name__ == "__main__":
    # Test the FASO client
    # In production, these will come from settings
    test_email = "your-email@example.com"
    test_password = "your-password"
    
    asyncio.run(test_faso_login(test_email, test_password))
