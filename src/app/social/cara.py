"""
Cara platform integration.
Posts artwork to cara.app via Playwright browser automation.

No public API — uses a persistent Chromium profile so you only log in once.
Run `python main.py cara-login` to set up the session, then all future
posts run headlessly without any manual interaction.
"""

import asyncio
from pathlib import Path
from urllib.parse import urlparse

from src.app.social.base import SocialPlatform, PostResult

CARA_HOME = "https://cara.app/home"
CARA_LOGIN_URL = "https://cara.app/login"


class CaraPlatform(SocialPlatform):
    """Cara social media platform integration via Playwright browser automation."""

    name = "cara"
    display_name = "Cara"
    supports_video = False
    supports_images = True
    max_text_length = 2000
    _is_stub = False

    def __init__(self):
        from config.settings import COOKIES_DIR
        self.profile_dir = COOKIES_DIR / "cara_browser_profile"
        self._marker = self.profile_dir / ".logged_in"

    def is_configured(self) -> bool:
        """Ready when the persistent browser profile has been set up via cara-login."""
        return self._marker.exists()

    def verify_credentials(self) -> bool:
        """
        Trust the marker file — the session is verified on the first post attempt.
        If the session has expired, post_image will clear the marker and tell the user.
        """
        return self.is_configured()

    def post_image(self, image_path: Path, text: str, alt_text: str = "") -> PostResult:
        """Post an image to Cara using Playwright browser automation."""
        if not self.is_configured():
            return PostResult(
                success=False,
                error="Cara session not set up. Run: python main.py cara-login"
            )
        try:
            return asyncio.run(self._post_image_async(image_path, text))
        except Exception as e:
            return PostResult(success=False, error=str(e))

    def post_video(self, video_path: Path, text: str) -> PostResult:
        """Video posting not yet implemented for Cara."""
        raise NotImplementedError("Cara video posting not yet implemented")

    def setup_session(self):
        """Open browser for manual login. Called by `python main.py cara-login`."""
        asyncio.run(self._setup_session_async())

    # -------------------------------------------------------------------------
    # Async internals
    # -------------------------------------------------------------------------

    async def _post_image_async(self, image_path: Path, text: str) -> PostResult:
        """Full Playwright posting flow."""
        from playwright.async_api import async_playwright
        from config.settings import SCREENSHOTS_DIR

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                viewport={"width": 1920, "height": 1080},
                args=["--disable-blink-features=AutomationControlled"],
            )
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            )

            try:
                page = context.pages[0] if context.pages else await context.new_page()

                # Navigate to Cara home
                await page.goto(CARA_HOME)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
                await page.screenshot(path=str(SCREENSHOTS_DIR / "cara_01_home.png"))

                # Session expired check — redirected away from cara.app
                if urlparse(page.url).hostname != "cara.app" or "/login" in page.url:
                    self._marker.unlink(missing_ok=True)
                    return PostResult(
                        success=False,
                        error="Cara session expired. Run: python main.py cara-login"
                    )

                # Wait for the React app to hydrate, then click the Post button.
                # domcontentloaded fires before hydration, so wait explicitly.
                post_btn = page.locator("a, button").filter(has_text="Post").first
                await post_btn.wait_for(state="attached", timeout=20_000)
                await post_btn.click(timeout=10_000)

                await asyncio.sleep(2)
                await page.screenshot(path=str(SCREENSHOTS_DIR / "cara_02_after_post_click.png"))

                # All remaining elements are inside a HeadlessUI dialog.
                # Use role="dialog" to scope INSIDE the content — this skips the
                # hidden focus-guard buttons that HeadlessUI adds around the dialog.
                # The outer div has no intrinsic size so skip wait_for;
                # the 2-second sleep above is sufficient.
                dialog = page.locator('[role="dialog"]')

                # The image select button is a plain SVG icon button (no text/id).
                # Use expect_file_chooser() so Playwright intercepts the native
                # file picker that the button opens, then sets our file directly.
                async with page.expect_file_chooser(timeout=10_000) as fc_info:
                    # Click the first real button inside the dialog (the photo icon)
                    await dialog.locator("button[type='button']").first.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(str(image_path))

                # Wait for the image preview and for the Post button to become enabled.
                # The submit button starts disabled="" and enables once an image is loaded.
                await asyncio.sleep(3)
                await page.screenshot(path=str(SCREENSHOTS_DIR / "cara_03_after_upload.png"))

                # wait_for only accepts attached/detached/visible/hidden — use expect() for enabled
                from playwright.async_api import expect as playwright_expect
                submit_btn = dialog.locator("button[type='submit']").first
                await playwright_expect(submit_btn).to_be_enabled(timeout=15_000)

                # Fill the caption text field
                try:
                    caption = dialog.locator("textarea").first
                    await caption.wait_for(state="attached", timeout=8_000)
                except Exception:
                    caption = dialog.locator("[contenteditable='true']").first
                    await caption.wait_for(state="attached", timeout=8_000)
                await caption.fill(text)
                await page.screenshot(path=str(SCREENSHOTS_DIR / "cara_04_after_caption.png"))

                # Tick "Add to portfolio"
                try:
                    portfolio_checkbox = dialog.locator("input[type='checkbox']").first
                    await portfolio_checkbox.wait_for(state="attached", timeout=5_000)
                    if not await portfolio_checkbox.is_checked():
                        await portfolio_checkbox.check(force=True)
                except Exception:
                    pass   # checkbox not found or already checked — continue

                await page.screenshot(path=str(SCREENSHOTS_DIR / "cara_05_before_submit.png"))

                # Click the Post submit button — force=True in case HeadlessUI styling
                # makes the button invisible to Playwright's hit-testing.
                await submit_btn.click(force=True, timeout=10_000)

                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)
                await page.screenshot(path=str(SCREENSHOTS_DIR / "cara_06_after_submit.png"))

                # Capture post URL if Cara navigated to it
                post_url = page.url if "cara.app" in page.url else None

                return PostResult(success=True, post_url=post_url)

            except Exception as e:
                # Save a failure screenshot for diagnosis
                try:
                    await page.screenshot(path=str(SCREENSHOTS_DIR / "cara_error.png"))
                except Exception:
                    pass
                raise

            finally:
                await context.close()

    async def _setup_session_async(self):
        """Open a visible browser so the user can log in manually. Saves the session."""
        from playwright.async_api import async_playwright
        from rich.console import Console

        console = Console()
        self.profile_dir.mkdir(parents=True, exist_ok=True)

        console.print("\n[bold cyan]═══ Cara Login Setup ═══[/bold cyan]\n")
        console.print("[yellow]This will open a browser. Log in to Cara manually.[/yellow]")
        console.print("[yellow]Once you can see your home feed, come back here and press Enter.[/yellow]\n")

        input("Press Enter to open browser...")

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                viewport={"width": 1920, "height": 1080},
                args=["--disable-blink-features=AutomationControlled"],
            )
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            )

            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(CARA_LOGIN_URL)
            await page.wait_for_load_state("domcontentloaded")

            console.print("[bold green]Browser open — log in now.[/bold green]")
            input("\nPress Enter when you can see your Cara home feed...")

            final_url = page.url
            await context.close()

        # Mark session as ready
        if "cara.app" in final_url and "/login" not in final_url:
            self._marker.write_text("ok")
            console.print("[bold green]Session saved. Cara is ready to post.[/bold green]")
        else:
            # Save anyway — user might have closed to a different URL
            self._marker.write_text("ok")
            console.print(f"[yellow]Final URL was: {final_url}[/yellow]")
            console.print("[yellow]Session saved. If posting fails, run cara-login again.[/yellow]")
