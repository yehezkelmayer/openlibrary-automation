"""Main test functions as specified in the exam requirements."""
import logging
import random
from playwright.async_api import Page
from pages import SearchPage, BookPage, ReadingListPage
from .performance_reporter import PerformanceReporter

logger = logging.getLogger(__name__)


async def search_books_by_title_under_year(
    page: Page,
    query: str,
    max_year: int,
    limit: int = 5
) -> list[str]:
    """
    Search for books by title and filter by publication year.
    Uses Advanced Search URL parameters for efficient filtering.

    Args:
        page: Playwright page instance
        query: Search query string
        max_year: Maximum publication year (inclusive)
        limit: Maximum number of URLs to collect (default: 5)

    Returns:
        List of book URLs matching the criteria
    """
    logger.info(f"Searching for '{query}' with max_year={max_year}, limit={limit}")

    search_page = SearchPage(page)

    # Use advanced search with year filter (via URL)
    await search_page.search_with_year_filter(query, max_year)

    # Check if there are results
    if not await search_page.has_results():
        logger.info("No search results found")
        return []

    # Get URLs - already filtered by year from advanced search
    urls = await search_page.get_book_urls(limit)

    logger.info(f"Found {len(urls)} books matching criteria")
    return urls


async def add_books_to_reading_list(
    page: Page,
    urls: list[str],
    screenshot_dir: str = "screenshots"
) -> int:
    """
    Add books to reading list with random status selection.

    Args:
        page: Playwright page instance
        urls: List of book URLs to add
        screenshot_dir: Directory to save screenshots

    Returns:
        Number of books successfully added
    """
    logger.info(f"Adding {len(urls)} books to reading list")

    book_page = BookPage(page)
    success_count = 0

    for idx, url in enumerate(urls, 1):
        try:
            await book_page.navigate_to_book(url)

            # Get book info for logging
            book_info = await book_page.get_book_info()
            title = book_info.get("title", "Unknown")

            # Randomly select status
            status = random.choice(["want_to_read", "already_read"])

            # Add to reading list
            selected_status = await book_page.add_to_reading_list(status)

            # Check if actually added
            if selected_status is not None:
                success_count += 1

            # Take screenshot with index to avoid overwrites
            safe_title = "".join(c if c.isalnum() else "_" for c in title[:25])
            screenshot_name = f"{idx:02d}_{safe_title}_{selected_status}"
            await book_page.take_screenshot(screenshot_name, screenshot_dir)

            logger.info(f"[{idx}/{len(urls)}] Added '{title}' with status: {selected_status}")

        except Exception as e:
            logger.error(f"Error adding book {url}: {e}")
            continue

    return success_count


async def assert_reading_list_count(
    page: Page,
    expected_count: int
) -> None:
    """
    Verify the reading list contains the expected number of books.

    Args:
        page: Playwright page instance
        expected_count: Expected number of books

    Raises:
        AssertionError: If count doesn't match expected
    """
    logger.info(f"Verifying reading list count. Expected: {expected_count}")

    reading_list = ReadingListPage(page)

    # Check both want-to-read and already-read lists
    total_count = 0

    for list_type in ["want-to-read", "already-read"]:
        await reading_list.navigate_to_reading_list(list_type)
        count = await reading_list.get_book_count()
        total_count += count
        logger.info(f"{list_type}: {count} books")

    logger.info(f"Total books in reading lists: {total_count}")

    assert total_count == expected_count, \
        f"Expected {expected_count} books, got {total_count}"

    logger.info("Reading list count verification passed!")


async def measure_page_performance(
    page: Page,
    url: str,
    threshold_ms: int,
    reporter: PerformanceReporter = None
) -> dict:
    """
    Measure page performance metrics.

    Args:
        page: Playwright page instance
        url: URL to measure
        threshold_ms: Performance threshold in milliseconds
        reporter: PerformanceReporter instance (optional)

    Returns:
        Dictionary with performance metrics
    """
    from pages import BasePage

    logger.info(f"Measuring performance for: {url}")

    base_page = BasePage(page)

    # Navigate and measure
    if url.startswith("http"):
        await page.goto(url, wait_until="load")
    else:
        await base_page.navigate(url)

    await base_page.wait_for_load()

    # Get performance metrics
    metrics = await base_page.measure_performance()

    # Check threshold
    load_time = metrics.get("load_time_ms")
    exceeded = False

    if load_time and load_time > threshold_ms:
        exceeded = True
        logger.warning(
            f"Threshold exceeded: {load_time}ms > {threshold_ms}ms (URL: {url})"
        )
    else:
        logger.info(f"Performance OK: {load_time}ms <= {threshold_ms}ms")

    # Add to reporter if provided
    if reporter:
        reporter.add_measurement(
            page_name=url,
            url=url,
            metrics=metrics,
            threshold_ms=threshold_ms,
            exceeded=exceeded
        )

    return {
        "load_time_ms": metrics.get("load_time_ms"),
        "dom_content_loaded_ms": metrics.get("dom_content_loaded_ms"),
        "first_paint_ms": metrics.get("first_paint_ms"),
        "threshold_ms": threshold_ms,
        "exceeded": exceeded
    }
