"""Base Page Object with common functionality."""
import logging
import sys
from pathlib import Path
from playwright.async_api import Page, expect

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from helpers.browser import Browser

logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all Page Objects."""

    BASE_URL = "https://openlibrary.org"

    def __init__(self, page: Page):
        """Initialize BasePage with Playwright page instance."""
        self.page = page

    @classmethod
    async def create(cls, page: Page | None = None) -> "BasePage":
        """Factory method to create page object with automatic page retrieval."""
        if page is None:
            page = await Browser.get_instance().get_page()
        instance = cls(page)
        return instance

    async def navigate(self, path: str = "") -> None:
        """Navigate to a specific path."""
        url = f"{self.BASE_URL}{path}"
        logger.info(f"Navigating to: {url}")
        await self.page.goto(url, wait_until="domcontentloaded")

    async def get_current_url(self) -> str:
        """Get the current page URL."""
        return self.page.url

    async def take_screenshot(self, name: str, directory: str = "screenshots") -> str:
        """Take a screenshot and save it."""
        Path(directory).mkdir(exist_ok=True)
        # Sanitize filename
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        filepath = f"{directory}/{safe_name}.png"
        await self.page.screenshot(path=filepath, full_page=True)
        logger.info(f"Screenshot saved: {filepath}")
        return filepath

    async def wait_for_load(self) -> None:
        """Wait for the page to fully load."""
        await self.page.wait_for_load_state("networkidle")

    async def get_element_text(self, selector: str) -> str:
        """Get text content of an element."""
        element = await self.page.wait_for_selector(selector)
        if element:
            return await element.inner_text()
        return ""

    async def click_element(self, selector: str) -> None:
        """Click on an element with wait."""
        await self.page.click(selector)

    async def fill_input(self, selector: str, text: str) -> None:
        """Fill an input field."""
        await self.page.fill(selector, text)

    async def is_element_visible(self, selector: str, timeout: int = 5000) -> bool:
        """Check if an element is visible."""
        try:
            await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    async def measure_performance(self) -> dict:
        """Measure page performance metrics."""
        metrics = await self.page.evaluate("""
            () => {
                const timing = performance.timing;
                const paint = performance.getEntriesByType('paint');

                const loadTime = timing.loadEventEnd - timing.navigationStart;
                const domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart;

                let firstPaint = 0;
                const fpEntry = paint.find(p => p.name === 'first-paint');
                if (fpEntry) {
                    firstPaint = fpEntry.startTime;
                }

                return {
                    load_time_ms: loadTime > 0 ? loadTime : null,
                    dom_content_loaded_ms: domContentLoaded > 0 ? domContentLoaded : null,
                    first_paint_ms: firstPaint > 0 ? firstPaint : null
                };
            }
        """)
        return metrics
