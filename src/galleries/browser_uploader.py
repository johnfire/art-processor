"""
Base class for browser-automated gallery site uploaders.
Provides shared Playwright infrastructure and form-filling utilities.
Each gallery site subclass only needs to implement its own navigation
and form-filling logic.
"""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page, BrowserContext
from rich.console import Console

from src.app_logger import get_logger

console = Console()


class BaseBrowserUploader(ABC):
    """
    Abstract base for Playwright-driven gallery site uploaders.

    Subclasses must define:
      - name          : short identifier used in log/screenshot prefixes
      - profile_dir   : Path to the persistent Chromium profile
      - dashboard_url : URL opened to verify the session is still valid
    """

    name: str = ""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._logger = get_logger(self.name or "gallery")

    # -------------------------------------------------------------------------
    # Abstract interface
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def profile_dir(self) -> Path:
        """Persistent Chromium profile directory for this site."""
        ...

    @property
    @abstractmethod
    def dashboard_url(self) -> str:
        """URL to navigate to in order to verify the session is valid."""
        ...

    # -------------------------------------------------------------------------
    # Browser lifecycle
    # -------------------------------------------------------------------------

    async def start_browser(self) -> bool:
        """
        Launch Chromium with the persistent profile and verify the session.
        Returns False if the profile is missing or the session has expired.
        """
        marker = self.profile_dir / ".logged_in"
        if not marker.exists():
            console.print(
                f"[red]No browser profile found for {self.name}. "
                f"Run the manual login command first.[/red]"
            )
            return False

        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            headless=self.headless,
            viewport={"width": 1920, "height": 1080},
            args=["--disable-blink-features=AutomationControlled"],
        )
        await self.context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        self.page = (
            self.context.pages[0] if self.context.pages else await self.context.new_page()
        )

        await self.page.goto(self.dashboard_url)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        current = self.page.url
        expected_host = urlparse(self.dashboard_url).hostname

        if "/login" in current.lower():
            console.print(f"[red]Session expired for {self.name}! Run the manual login command again.[/red]")
            await self.close_browser()
            return False

        if urlparse(current).hostname != expected_host:
            console.print(f"[red]Cannot reach {self.name} dashboard. Run the manual login command again.[/red]")
            await self.close_browser()
            return False

        console.print(f"[green]Browser started, {self.name} session valid[/green]")
        return True

    async def close_browser(self):
        """Close the browser context and Playwright instance."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_browser()

    # -------------------------------------------------------------------------
    # Shared form helpers
    # -------------------------------------------------------------------------

    async def _fill_text_field(self, selector: str, value: str):
        """Clear a text input and type a new value."""
        try:
            field = await self.page.wait_for_selector(selector, timeout=3000)
            await field.click(click_count=3)
            await field.fill(value)
        except Exception as e:
            console.print(f"[yellow]Warning: could not fill {selector}: {e}[/yellow]")

    async def _select_dropdown(self, selector: str, value: str):
        """Select a dropdown option by exact visible label."""
        try:
            await self.page.select_option(selector, label=value)
        except Exception as e:
            console.print(
                f"[yellow]Warning: could not select '{value}' in {selector}: {e}[/yellow]"
            )

    async def _select_dropdown_fuzzy(self, selector: str, value: str):
        """Select a dropdown option using normalised fuzzy label matching."""
        try:
            await self.page.select_option(selector, label=value)
            return
        except Exception:
            pass

        try:
            options = await self.page.eval_on_selector_all(
                f"{selector} option",
                "els => els.map(e => e.textContent.trim())",
            )
            normalized = self._normalize_for_match(value)
            for option in options:
                if option and self._normalize_for_match(option) == normalized:
                    await self.page.select_option(selector, label=option)
                    console.print(f"[green]Matched '{value}' → '{option}'[/green]")
                    return
            console.print(
                f"[yellow]Warning: no fuzzy match for '{value}' in {selector}[/yellow]"
            )
        except Exception as e:
            console.print(
                f"[yellow]Warning: fuzzy select failed for '{value}': {e}[/yellow]"
            )

    @staticmethod
    def _normalize_for_match(text: str) -> str:
        """Normalise text for fuzzy dropdown matching (lowercase, strip punctuation)."""
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

    async def _fill_description(self, description: str):
        """
        Fill a rich text description editor.
        Tries TinyMCE JS API first, then textarea fallback, then iframe body.
        """
        html_content = self.markdown_to_html(description)
        try:
            result = await self.page.evaluate(f"""
                () => {{
                    if (typeof tinymce !== 'undefined' && tinymce.get("Description")) {{
                        tinymce.get("Description").setContent({json.dumps(html_content)});
                        return true;
                    }}
                    return false;
                }}
            """)
            if result:
                console.print("[green]Description filled via TinyMCE API[/green]")
                return

            textarea = await self.page.query_selector('textarea[name="Description"]')
            if textarea:
                await textarea.fill(html_content)
                console.print("[green]Description filled via textarea[/green]")
                return

            iframe = await self.page.query_selector("iframe#Description_ifr")
            if iframe:
                frame = await iframe.content_frame()
                if frame:
                    await frame.evaluate(
                        f"document.body.innerHTML = {json.dumps(html_content)}"
                    )
                    console.print("[green]Description filled via iframe[/green]")
                    return

            console.print("[yellow]Warning: could not fill description field[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: description fill failed: {e}[/yellow]")

    async def _take_error_screenshot(self, step: str):
        """Save a debug screenshot to the configured screenshots directory."""
        from config.settings import SCREENSHOTS_DIR
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = SCREENSHOTS_DIR / f"{self.name}_error_{step}_{timestamp}.png"
        try:
            await self.page.screenshot(path=str(path), full_page=True)
            console.print(f"[yellow]Error screenshot: {path}[/yellow]")
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Static helpers (available on subclasses without an instance)
    # -------------------------------------------------------------------------

    @staticmethod
    def get_image_path(metadata: Dict[str, Any]) -> Optional[str]:
        """Return the 'big' image path from metadata (handles string or list)."""
        big = metadata.get("files", {}).get("big")
        if isinstance(big, list):
            return big[0] if big else None
        return big

    @staticmethod
    def extract_year(creation_date: Optional[str]) -> str:
        """Extract a 4-digit year from an ISO date string, or return the current year."""
        if creation_date and len(creation_date) >= 4:
            return creation_date[:4]
        return str(datetime.now().year)

    @staticmethod
    def markdown_to_html(text: str) -> str:
        """Convert simple markdown (**bold**, *italic*, paragraphs) to HTML."""
        if not text:
            return ""
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        paragraphs = html.split("\n\n")
        return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())
