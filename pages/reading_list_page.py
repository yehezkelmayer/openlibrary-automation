"""Reading List Page Object for OpenLibrary reading list functionality."""
import logging
from playwright.async_api import Page
from .base_page import BasePage

logger = logging.getLogger(__name__)


class ReadingListPage(BasePage):
    """Page Object for OpenLibrary reading list page."""

    # Locators - Updated for actual OpenLibrary structure
    READING_LIST_PATH = "/account/books/want-to-read"
    # Multiple selectors for book items
    BOOK_ITEMS = "li:has(h3 a)"
    BOOK_COUNT_TEXT = ".results-count, .list-header, .book-count, h2"
    NO_BOOKS_MESSAGE = ".empty-list, .no-books, p:has-text('No books')"
    BOOK_TITLE_IN_LIST = ".resultTitle, .book-title, a.title, h3"
    REMOVE_BOOK_BTN = ".remove-book, button[title*='Remove'], .remove-from-list"
    TAB_WANT_TO_READ = "a[href*='want-to-read']"
    TAB_ALREADY_READ = "a[href*='already-read']"
    TAB_CURRENTLY_READING = "a[href*='currently-reading']"

    def __init__(self, page: Page):
        """Initialize ReadingListPage."""
        super().__init__(page)

    async def navigate_to_want_to_read(self) -> None:
        """Navigate to 'Want to Read' list."""
        await self.navigate("/account/books/want-to-read")
        await self.page.wait_for_load_state("domcontentloaded")

    async def navigate_to_already_read(self) -> None:
        """Navigate to 'Already Read' list."""
        await self.navigate("/account/books/already-read")
        await self.page.wait_for_load_state("domcontentloaded")

    async def navigate_to_reading_list(self, list_type: str = "want-to-read") -> None:
        """
        Navigate to a specific reading list.

        Args:
            list_type: "want-to-read", "already-read", or "currently-reading"
        """
        await self.navigate(f"/account/books/{list_type}")
        await self.page.wait_for_load_state("domcontentloaded")

    async def get_book_count(self) -> int:
        """
        Get the number of books in the current reading list.

        Returns:
            Number of books in the list
        """
        try:
            # Wait a bit for the page to load
            await self.page.wait_for_timeout(300)

            # Try to find book items
            items = await self.page.query_selector_all(self.BOOK_ITEMS)
            count = len(items)

            logger.info(f"Found {count} books in reading list")
            return count

        except Exception as e:
            logger.warning(f"Error getting book count: {e}")
            return 0

    async def get_all_book_titles(self) -> list[str]:
        """Get all book titles in the reading list."""
        titles = []
        try:
            items = await self.page.query_selector_all(self.BOOK_ITEMS)
            for item in items:
                title_el = await item.query_selector(self.BOOK_TITLE_IN_LIST)
                if title_el:
                    title = await title_el.inner_text()
                    titles.append(title.strip())
        except Exception as e:
            logger.warning(f"Error getting book titles: {e}")
        return titles

    async def is_book_in_list(self, title: str) -> bool:
        """Check if a book with given title is in the list."""
        titles = await self.get_all_book_titles()
        return any(title.lower() in t.lower() for t in titles)

    async def is_list_empty(self) -> bool:
        """Check if the reading list is empty."""
        count = await self.get_book_count()
        return count == 0

    async def get_total_books_all_lists(self) -> dict:
        """Get book counts for all reading lists."""
        counts = {}

        for list_type in ["want-to-read", "already-read", "currently-reading"]:
            await self.navigate_to_reading_list(list_type)
            counts[list_type] = await self.get_book_count()

        return counts

    async def remove_book_from_list(self, list_type: str = "want-to-read") -> bool:
        """Remove one book from the current list. Returns True if a book was removed."""
        try:
            count_before = await self.get_book_count()
            if count_before == 0:
                return False

            # Try multiple selectors - different lists have different buttons
            remove_selectors = [
                "button.remove-from-list",  # want-to-read list
                "form.reading-log.primary-action button",  # already-read list
            ]

            for selector in remove_selectors:
                remove_btn = await self.page.query_selector(selector)
                if remove_btn and await remove_btn.is_visible():
                    # Click and wait for response (not navigation)
                    async with self.page.expect_response(lambda r: "reading" in r.url or "books" in r.url) as response_info:
                        await remove_btn.click()

                    # Wait for response to complete
                    response = await response_info.value
                    await self.page.wait_for_timeout(200)

                    # Navigate back to list
                    await self.navigate_to_reading_list(list_type)

                    # Verify book was removed
                    count_after = await self.get_book_count()
                    if count_after < count_before:
                        return True
                    else:
                        logger.warning(f"Book not removed: {count_before} -> {count_after}")
                        return False

            return False
        except Exception as e:
            logger.warning(f"Error removing book: {e}")
            # Try to navigate back to list
            try:
                await self.navigate_to_reading_list(list_type)
            except Exception:
                pass
            return False

    async def clear_reading_list(self, list_type: str = "want-to-read") -> int:
        """
        Clear all books from a reading list.

        Args:
            list_type: "want-to-read", "already-read", or "currently-reading"

        Returns:
            Number of books removed
        """
        await self.navigate_to_reading_list(list_type)
        removed = 0
        max_attempts = 50  # Safety limit

        while max_attempts > 0:
            count = await self.get_book_count()
            if count == 0:
                break

            if await self.remove_book_from_list(list_type):
                removed += 1
            else:
                break

            max_attempts -= 1

        logger.info(f"Removed {removed} books from {list_type}")
        return removed

    async def clear_all_reading_lists(self) -> dict:
        """Clear all reading lists. Returns counts of removed books."""
        removed = {}
        for list_type in ["want-to-read", "already-read"]:
            removed[list_type] = await self.clear_reading_list(list_type)
        return removed
