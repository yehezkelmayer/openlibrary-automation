"""Book Page Object for individual book pages."""
import logging
import random
from playwright.async_api import Page
from .base_page import BasePage

logger = logging.getLogger(__name__)

SELECTORS = {
    "master_button": "button.book-progress-btn.primary-action > span.btn-text",
    "master_button_active": "button.book-progress-btn.primary-action.activated > span.btn-text",
    "arrow_button": "div.generic-dropper__actions > a",
    "reading_buttons": "div.read-statuses > form.reading-log > button.nostyle-btn",
    "dropper_wrapper": "div.generic-dropper-wrapper.my-books-dropper",
}


class BookPage(BasePage):
    """Page Object for OpenLibrary book page."""

    # Multiple selectors for book title - different page types have different structures
    BOOK_TITLE_SELECTORS = [
        "h1.work-title",
        "h1[itemprop='name']",
        ".workTitle h1",
        "h1.title",
        ".book-title h1",
        "h1",  # Fallback to any h1
    ]

    def __init__(self, page: Page):
        """Initialize BookPage."""
        super().__init__(page)

    async def navigate_to_book(self, url: str) -> None:
        """Navigate to a specific book page."""
        logger.info(f"Navigating to book: {url}")
        await self.page.goto(url)
        await self.page.wait_for_load_state("domcontentloaded")

        # Wait for the reading list dropdown to appear
        try:
            await self.page.wait_for_selector(SELECTORS["dropper_wrapper"], timeout=5000)
        except Exception:
            logger.warning("Reading list dropdown not found - user might not be logged in")

    async def get_book_title(self) -> str:
        """Get the book title."""
        for selector in self.BOOK_TITLE_SELECTORS:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    title = await element.inner_text()
                    if title and title.strip():
                        return title.strip()
            except Exception:
                continue
        return "Unknown Title"

    async def _click_master_button(self, target_text: str) -> bool | str:
        """
        Click the main reading button if it matches target text.
        Returns True if clicked, False if not found, or current status text if already set.
        """
        try:
            await self.page.wait_for_selector(SELECTORS["master_button"], timeout=5000)
        except Exception:
            logger.warning("Master button not found")
            return False

        # Check if already activated with this status
        active_btn = await self.page.query_selector(SELECTORS["master_button_active"])
        if active_btn:
            current_text = (await active_btn.inner_text()).strip().lower()
            if current_text == target_text.lower():
                logger.info(f"Book already marked as '{target_text}'")
                return True
            else:
                # Already has different status
                return current_text

        # Not activated - try to click
        master_btn = await self.page.query_selector(SELECTORS["master_button"])
        if master_btn:
            btn_text = (await master_btn.inner_text()).strip().lower()
            if btn_text == target_text.lower():
                await master_btn.click()
                await self.page.wait_for_timeout(300)
                logger.info(f"Clicked master button: {target_text}")
                return True

        return False

    async def _expand_dropdown(self) -> None:
        """Expand the reading options dropdown."""
        arrow = await self.page.query_selector(SELECTORS["arrow_button"])
        if arrow:
            await arrow.click()
            await self.page.wait_for_timeout(200)

    async def _click_reading_button(self, target_text: str) -> bool:
        """Click a specific reading status button from the dropdown."""
        buttons = await self.page.query_selector_all(SELECTORS["reading_buttons"])

        for btn in buttons:
            btn_text = (await btn.inner_text()).strip().lower()
            if btn_text == target_text.lower():
                # Check if visible, expand dropdown if not
                if not await btn.is_visible():
                    await self._expand_dropdown()
                    await self.page.wait_for_timeout(150)

                await btn.click()
                await self.page.wait_for_timeout(300)
                logger.info(f"Clicked reading button: {target_text}")
                return True

        return False

    async def add_to_reading_list(self, status: str = "random") -> str:
        """
        Add the book to reading list with specified status.

        Args:
            status: "want_to_read", "already_read", or "random"

        Returns:
            The status that was selected
        """
        if status == "random":
            status = random.choice(["want_to_read", "already_read"])

        # Map internal status to button text
        status_map = {
            "want_to_read": "Want to Read",
            "already_read": "Already Read",
            "currently_reading": "Currently Reading"
        }
        target_text = status_map.get(status, "Want to Read")

        logger.info(f"Adding book to reading list with status: {target_text}")

        # Try master button first
        result = await self._click_master_button(target_text)

        if result is True:
            logger.info(f"Successfully added with status: {status}")
            return status

        if result is False or isinstance(result, str):
            # Try the dropdown buttons
            if await self._click_reading_button(target_text):
                logger.info(f"Successfully added with status: {status}")
                return status

        logger.warning(f"Could not add book with status: {status}")
        return None  # Return None to indicate failure

    async def get_book_info(self) -> dict:
        """Get book information."""
        title = await self.get_book_title()
        url = await self.get_current_url()

        return {
            "title": title,
            "url": url,
        }
