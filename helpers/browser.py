"""Browser Singleton for managing Playwright browser instance."""
import os
from playwright.async_api import async_playwright, Browser as PWBrowser, BrowserContext, Page


class Browser:
    """Singleton class for browser management - one browser for entire test session."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._playwright = None
        self._browser: PWBrowser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._current_storage_state: str | None = None  # Track current auth state
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "Browser":
        """Get the singleton instance."""
        return cls()

    @property
    def headless(self) -> bool:
        """Check if browser should run headless."""
        return os.getenv("HEADLESS", "true").lower() == "true"

    async def get_browser(self) -> PWBrowser:
        """Get or create browser instance."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                channel="chrome",
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
        return self._browser

    async def get_context(self, storage_state: str | None = None) -> BrowserContext:
        """Get or create browser context with optional auth state."""
        # Check if storage_state changed - need to recreate context
        if self._context is not None and storage_state != self._current_storage_state:
            # Close old context and page
            if self._page is not None and not self._page.is_closed():
                await self._page.close()
                self._page = None
            await self._context.close()
            self._context = None

        if self._context is None:
            browser = await self.get_browser()

            context_options = {
                "viewport": {"width": 1920, "height": 1080}
            }

            if storage_state and os.path.exists(storage_state):
                context_options["storage_state"] = storage_state

            self._context = await browser.new_context(**context_options)
            self._current_storage_state = storage_state

        return self._context

    async def get_page(self, storage_state: str | None = None) -> Page:
        """Get or create page instance."""
        if self._page is None or self._page.is_closed():
            context = await self.get_context(storage_state)
            self._page = await context.new_page()
        return self._page

    async def new_page(self) -> Page:
        """Create a new page (tab) in the same context."""
        context = await self.get_context()
        return await context.new_page()

    async def close(self) -> None:
        """Close all browser resources."""
        if self._page is not None and not self._page.is_closed():
            await self._page.close()
            self._page = None

        if self._context is not None:
            await self._context.close()
            self._context = None

        if self._browser is not None:
            await self._browser.close()
            self._browser = None

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def reset(self) -> None:
        """Reset browser state (close and prepare for new session)."""
        await self.close()
        self._initialized = False
        Browser._instance = None
