"""Search Page Object for OpenLibrary search functionality."""
import logging
import re
from playwright.async_api import Page
from .base_page import BasePage

logger = logging.getLogger(__name__)


class SearchPage(BasePage):
    """Page Object for OpenLibrary search page."""

    # Locators
    SEARCH_INPUT = "input[name='q']"
    SEARCH_BUTTON = "input.search-bar-submit[type='submit'], button[type='submit']"
    SEARCH_RESULTS = "li.searchResultItem"
    BOOK_LINK = "h3.booktitle > a"
    BOOK_TITLE = "h3.booktitle"
    NO_RESULTS = "text=No results found"
    NEXT_PAGE = "nav > a.pagination-item.pagination-arrow:last-of-type"

    def __init__(self, page: Page):
        """Initialize SearchPage."""
        super().__init__(page)
        self._max_year = None  # For year filtering

    async def navigate_to_search(self) -> None:
        """Navigate to the home page for search."""
        await self.page.goto(f"{self.BASE_URL}/")
        await self.page.wait_for_load_state("domcontentloaded")

    async def search_with_year_filter(self, title: str, max_year: int) -> None:
        """
        Search by title using URL parameters.
        Year filtering is done when extracting results.
        """
        self._max_year = max_year  # Store for filtering in get_book_urls

        # Simple title search
        search_url = f"{self.BASE_URL}/search?title={title}"
        logger.info(f"Search URL: {search_url}")

        # Navigate directly to search results
        await self.page.goto(search_url)
        await self.page.wait_for_load_state("domcontentloaded")

        # Wait for search results to appear
        try:
            await self.page.wait_for_selector(self.SEARCH_RESULTS, timeout=10000)
        except Exception:
            # No results found, wait a bit for page to settle
            await self.page.wait_for_timeout(500)

    async def get_search_results(self) -> list:
        """Get all search result elements."""
        await self.page.wait_for_load_state("domcontentloaded")
        return await self.page.query_selector_all(self.SEARCH_RESULTS)

    async def get_book_urls(self, limit: int = 5) -> list[str]:
        """
        Get book URLs from search results, filtered by year if set.
        Supports pagination - moves to next page if needed.
        """
        urls = []
        max_pages = 5  # Safety limit to avoid infinite loops

        for page_num in range(max_pages):
            if len(urls) >= limit:
                break

            results = await self.get_search_results()
            if not results:
                break

            for item in results:
                if len(urls) >= limit:
                    break

                try:
                    # Get the book title
                    title_el = await item.query_selector(self.BOOK_TITLE)
                    title = await title_el.inner_text() if title_el else ""

                    # Check year if filter is set
                    if self._max_year:
                        # Find "First published in YYYY" text
                        item_text = await item.inner_text()
                        year_match = re.search(r'(?:First published|published).*?(\d{4})', item_text, re.IGNORECASE)
                        if year_match:
                            year = int(year_match.group(1))
                            if year > self._max_year:
                                logger.debug(f"Skipping {title.strip()} - year {year} > {self._max_year}")
                                continue
                        else:
                            # No year found - skip when filtering by year
                            logger.debug(f"Skipping {title.strip()} - no year found")
                            continue

                    link = await item.query_selector(self.BOOK_LINK)
                    if link:
                        href = await link.get_attribute("href")
                        if href and "/works/" in href:
                            work_part = href.split("?")[0]
                            full_url = f"{self.BASE_URL}{work_part}" if work_part.startswith("/") else work_part
                            if full_url not in urls:  # Avoid duplicates
                                urls.append(full_url)
                                logger.info(f"Found book: {title.strip()} -> {full_url}")
                except Exception as e:
                    logger.warning(f"Error getting book URL: {e}")
                    continue

            # Go to next page if we need more results
            if len(urls) < limit:
                if not await self._go_to_next_page():
                    logger.info("No more pages available")
                    break
                logger.info(f"Moving to page {page_num + 2}")

        return urls

    async def _go_to_next_page(self) -> bool:
        """Click next page button. Returns True if successful."""
        try:
            next_btn = await self.page.query_selector(self.NEXT_PAGE)
            if next_btn:
                await next_btn.click()
                await self.page.wait_for_load_state("domcontentloaded")
                await self.page.wait_for_timeout(300)
                return True
            return False
        except Exception as e:
            logger.warning(f"Error navigating to next page: {e}")
            return False

    async def has_results(self) -> bool:
        """Check if there are any search results."""
        try:
            no_results = await self.page.query_selector(self.NO_RESULTS)
            if no_results:
                return False
            results = await self.page.query_selector_all(self.SEARCH_RESULTS)
            return len(results) > 0
        except Exception:
            return False
