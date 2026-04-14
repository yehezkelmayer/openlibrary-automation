"""Performance measurement helper - separated from BasePage for SRP."""
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class PerformanceHelper:
    """Helper class for measuring page performance metrics."""

    def __init__(self, page: Page):
        """Initialize with Playwright page instance."""
        self.page = page

    async def measure(self) -> dict:
        """
        Measure page performance metrics using Navigation Timing API.

        Returns:
            Dictionary with load_time_ms, dom_content_loaded_ms, first_paint_ms
        """
        metrics = await self.page.evaluate("""
            () => {
                // Use modern Navigation Timing API (performance.timing is deprecated)
                const navEntries = performance.getEntriesByType('navigation');
                const paintEntries = performance.getEntriesByType('paint');

                if (navEntries.length === 0) {
                    return {
                        load_time_ms: null,
                        dom_content_loaded_ms: null,
                        first_paint_ms: null
                    };
                }

                const nav = navEntries[0];
                const loadTime = nav.loadEventEnd - nav.startTime;
                const domContentLoaded = nav.domContentLoadedEventEnd - nav.startTime;

                let firstPaint = 0;
                const fpEntry = paintEntries.find(p => p.name === 'first-paint');
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

    async def measure_with_navigation(self, url: str) -> dict:
        """
        Navigate to URL and measure performance.

        Args:
            url: URL to navigate to and measure

        Returns:
            Dictionary with performance metrics
        """
        logger.info(f"Measuring performance for: {url}")

        await self.page.goto(url, wait_until="load")
        await self.page.wait_for_load_state("domcontentloaded")

        return await self.measure()
