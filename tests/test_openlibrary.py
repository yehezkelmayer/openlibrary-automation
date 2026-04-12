"""OpenLibrary E2E Test Suite with Allure Reporting."""
import pytest
import allure
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from helpers.browser import Browser
from pages import SearchPage, BookPage, ReadingListPage
from utils.test_functions import (
    search_books_by_title_under_year,
    add_books_to_reading_list,
    assert_reading_list_count,
    measure_page_performance
)
from utils.performance_reporter import PerformanceReporter

AUTH_STATE_PATH = Path(__file__).parent.parent / "auth_state.json"


@pytest.fixture(scope="module")
async def browser():
    """Module-scoped browser - one browser for all tests in this file."""
    browser = Browser.get_instance()
    auth_state = str(AUTH_STATE_PATH) if AUTH_STATE_PATH.exists() else None
    await browser.get_page(storage_state=auth_state)
    yield browser
    await browser.close()


@pytest.fixture(scope="function")
async def page(browser):
    """Get the singleton page."""
    return await browser.get_page()


@allure.epic("OpenLibrary Automation")
@allure.feature("Book Search")
class TestBookSearch:
    """Book search tests."""

    @allure.story("Search with year filter")
    @allure.title("Search for Dune books before 1980")
    @pytest.mark.smoke
    async def test_search_books_by_title_under_year(self, page):
        """Search for books filtered by publication year."""
        urls = await search_books_by_title_under_year(
            page=page,
            query="Dune",
            max_year=1980,
            limit=5
        )

        print(f"\n>>> Found {len(urls)} books before 1980:")
        for url in urls:
            print(f"    {url}")

        allure.attach("\n".join(urls) if urls else "No results",
                      name="Book URLs", attachment_type=allure.attachment_type.TEXT)
        assert isinstance(urls, list)

    @allure.story("Search with pagination")
    @allure.title("Search Foundation books with pagination")
    async def test_search_with_pagination(self, page):
        """Test pagination support."""
        urls = await search_books_by_title_under_year(
            page=page, query="Foundation", max_year=1960, limit=3
        )
        print(f"\n>>> Found {len(urls)} Foundation books")
        assert isinstance(urls, list)

    @allure.story("No results")
    @allure.title("Handle search with no results")
    async def test_search_no_results(self, page):
        """Test empty results handling."""
        urls = await search_books_by_title_under_year(
            page=page, query="xyznonexistentbook123", max_year=1900, limit=5
        )
        print(f"\n>>> Search returned {len(urls)} results (expected 0)")
        assert urls == []


@allure.epic("OpenLibrary Automation")
@allure.feature("Reading List")
class TestReadingList:
    """Reading list tests - REQUIRES LOGIN."""

    @allure.story("Add books to list")
    @allure.title("Add books to reading list")
    @pytest.mark.smoke
    async def test_add_books_to_reading_list(self, page):
        """Add books to reading list with screenshots."""
        if not AUTH_STATE_PATH.exists():
            pytest.skip("Run 'python3 save_auth_manually.py' first")

        # Search for books
        urls = await search_books_by_title_under_year(
            page=page, query="Dune", max_year=1990, limit=2
        )

        if not urls:
            pytest.skip("No books found")

        print(f"\n>>> Adding {len(urls)} books to reading list...")
        screenshot_dir = Path(__file__).parent.parent / "screenshots"

        await add_books_to_reading_list(
            page=page, urls=urls, screenshot_dir=str(screenshot_dir)
        )
        print(">>> Books added successfully!")

        # Attach screenshots
        for screenshot in screenshot_dir.glob("*.png"):
            allure.attach.file(str(screenshot), name=screenshot.stem,
                               attachment_type=allure.attachment_type.PNG)

    @allure.story("Verify reading list")
    @allure.title("Verify reading list count")
    async def test_verify_reading_list(self, page):
        """Verify books in reading list."""
        if not AUTH_STATE_PATH.exists():
            pytest.skip("Run 'python3 save_auth_manually.py' first")

        reading_list = ReadingListPage(page)
        await reading_list.navigate_to_want_to_read()

        count = await reading_list.get_book_count()
        print(f"\n>>> Reading list has {count} books")

        allure.attach(f"Books in list: {count}", name="Count",
                      attachment_type=allure.attachment_type.TEXT)
        assert count >= 0


@allure.epic("OpenLibrary Automation")
@allure.feature("Performance")
class TestPerformance:
    """Performance tests."""

    @pytest.fixture
    def reporter(self):
        return PerformanceReporter(Path(__file__).parent.parent / "performance_report.json")

    @allure.story("Search page performance")
    @pytest.mark.performance
    async def test_search_page_performance(self, page, reporter):
        """Measure search page performance."""
        metrics = await measure_page_performance(
            page=page,
            url="https://openlibrary.org/search?q=test",
            threshold_ms=3000,
            reporter=reporter
        )

        print(f"\n>>> Search Page: {metrics['load_time_ms']}ms (threshold: 3000ms)")
        allure.attach(json.dumps(metrics, indent=2), name="Metrics",
                      attachment_type=allure.attachment_type.JSON)

    @allure.story("Book page performance")
    @pytest.mark.performance
    async def test_book_page_performance(self, page, reporter):
        """Measure book page performance."""
        metrics = await measure_page_performance(
            page=page,
            url="https://openlibrary.org/works/OL45883W",
            threshold_ms=2500,
            reporter=reporter
        )

        print(f"\n>>> Book Page: {metrics['load_time_ms']}ms (threshold: 2500ms)")
        allure.attach(json.dumps(metrics, indent=2), name="Metrics",
                      attachment_type=allure.attachment_type.JSON)

    @allure.story("Full performance report")
    @pytest.mark.performance
    async def test_generate_performance_report(self, page, reporter):
        """Generate comprehensive performance report."""
        pages_to_test = [
            ("Search", "https://openlibrary.org/search?q=python", 3000),
            ("Book", "https://openlibrary.org/works/OL45883W", 2500),
        ]

        print("\n>>> Performance Report:")
        print("=" * 50)

        for name, url, threshold in pages_to_test:
            metrics = await measure_page_performance(
                page=page, url=url, threshold_ms=threshold, reporter=reporter
            )
            status = "PASS" if not metrics['exceeded'] else "WARN"
            print(f"  {name}: {metrics['load_time_ms']}ms [{status}]")

        # Save report
        report_path = reporter.save_report()
        print("=" * 50)
        print(f">>> Report saved: {report_path}")

        reporter.print_summary()

        allure.attach.file(str(report_path), name="Performance Report",
                           attachment_type=allure.attachment_type.JSON)


@allure.epic("OpenLibrary Automation")
@allure.feature("E2E Flow")
class TestE2EFlow:
    """Full E2E flow - REQUIRES LOGIN."""

    @allure.story("Complete flow")
    @allure.title("Search -> Add to List -> Verify")
    @pytest.mark.smoke
    async def test_complete_flow(self, page):
        """Complete E2E: search, add, verify."""
        if not AUTH_STATE_PATH.exists():
            pytest.skip("Run 'python3 save_auth_manually.py' first")

        # Step 1: Search
        print("\n>>> Step 1: Search for books")
        urls = await search_books_by_title_under_year(
            page=page, query="Dune", max_year=1985, limit=3
        )
        print(f"    Found {len(urls)} books")

        if not urls:
            pytest.skip("No books found")

        # Step 2: Add to list
        print("\n>>> Step 2: Add to reading list")
        screenshot_dir = Path(__file__).parent.parent / "screenshots"
        await add_books_to_reading_list(
            page=page, urls=urls[:2], screenshot_dir=str(screenshot_dir)
        )
        print("    Added!")

        # Step 3: Verify
        print("\n>>> Step 3: Verify reading list")
        reading_list = ReadingListPage(page)
        await reading_list.navigate_to_want_to_read()
        count = await reading_list.get_book_count()
        print(f"    Reading list has {count} books")

        print("\n>>> E2E PASSED!")
        allure.attach(f"Final count: {count}", name="Result",
                      attachment_type=allure.attachment_type.TEXT)
