"""
OpenLibrary Automation - Main Entry Point
Run with: python main.py
"""
import asyncio
import logging
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

from helpers.browser import Browser
from helpers.report_generator import ReportGenerator
from pages import SearchPage, BookPage, ReadingListPage
from utils.test_functions import (
    search_books_by_title_under_year,
    add_books_to_reading_list,
    assert_reading_list_count,
    measure_page_performance
)
from utils.performance_reporter import PerformanceReporter
from utils.data_loader import DataLoader

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
REPORTS_DIR = Path(__file__).parent / "reports"


async def auto_login(page) -> bool:
    """
    Automatically login using credentials from .env file.
    Returns True if login successful, False otherwise.
    """
    import asyncio

    email = os.getenv("OL_EMAIL")
    password = os.getenv("OL_PASSWORD")

    if not email or not password:
        logger.info("No credentials in .env, skipping auto-login")
        return False

    print(">>> Attempting auto-login with .env credentials...")

    try:
        # Step 1: Find and click "Log In" button from current page
        login_buttons = await page.query_selector_all("a.btn")
        login_element = None

        for button in login_buttons:
            text = await button.inner_text()
            if text.strip().lower() == "log in":
                login_element = button
                break

        if login_element is None:
            print(">>> Log In button not found, trying direct navigation")
            await page.goto("https://openlibrary.org/account/login")
        else:
            await login_element.click()

        # Step 2: Wait for login form
        await page.wait_for_selector("form[id='register'].login.olform", timeout=5000)

        # Step 3: Fill form via form element
        form = await page.query_selector("form[id='register'].login.olform")
        if form is None:
            print(">>> Login form not found")
            return False

        email_input = await form.query_selector("input[name='username']")
        password_input = await form.query_selector("input[name='password']")

        if email_input is None or password_input is None:
            print(">>> Form inputs not found")
            return False

        await email_input.fill(email)
        await password_input.fill(password)

        # Step 4: Submit via button
        submit_button = await form.query_selector("button[type='submit']")
        if submit_button is None:
            print(">>> Submit button not found")
            return False

        await submit_button.click()

        # Step 5: Wait for login to process
        await asyncio.sleep(5)

        # Step 6: Verify login - check if "Log In" button is gone
        login_buttons = await page.query_selector_all("a.btn")
        is_logged_in = True

        for button in login_buttons:
            text = await button.inner_text()
            if text.strip().lower() == "log in":
                is_logged_in = False
                break

        if is_logged_in:
            print(">>> Auto-login successful!")
            # Save auth state for future runs
            await page.context.storage_state(path=str(AUTH_STATE_PATH))
            logger.info(f"Auth state saved to {AUTH_STATE_PATH}")
            return True
        else:
            print(">>> Auto-login failed (wrong credentials or CAPTCHA)")
            return False

    except Exception as e:
        logger.error(f"Auto-login error: {e}")
        return False


async def main():
    """Main test orchestrator."""
    print("=" * 60)
    print("OpenLibrary Automation Test Suite")
    print("=" * 60)

    # Clear screenshots from previous runs
    if SCREENSHOTS_DIR.exists():
        shutil.rmtree(SCREENSHOTS_DIR)
    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    # Initialize
    browser = Browser.get_instance()
    report = ReportGenerator(screenshots_dir=str(SCREENSHOTS_DIR))
    perf_reporter = PerformanceReporter(report_dir=str(REPORTS_DIR / "performance"))

    # Load test data
    data_loader = DataLoader()
    test_config = data_loader.load_yaml("test_data.yaml")

    try:
        # Get page with auth state if available
        auth_state = str(AUTH_STATE_PATH) if AUTH_STATE_PATH.exists() else None
        page = await browser.get_page(storage_state=auth_state)

        # Navigate to home
        await page.goto("https://openlibrary.org")
        await page.wait_for_load_state("domcontentloaded")

        # Check if logged in
        is_logged_in = await page.query_selector("a[href*='/people/']") is not None

        # If not logged in, try auto-login with .env credentials
        if not is_logged_in:
            is_logged_in = await auto_login(page)

        print(f"\n>>> Logged in: {is_logged_in}")

        if not is_logged_in:
            print(">>> WARNING: Not logged in.")
            print(">>> Options:")
            print(">>>   1. Add OL_EMAIL and OL_PASSWORD to .env file")
            print(">>>   2. Run 'python setup_auth.py' for manual login")
            print(">>> Continuing with limited functionality...\n")

        # Create Page Objects once and reuse them
        search_page = SearchPage(page)
        book_page = BookPage(page)
        reading_list = ReadingListPage(page)

        # ============================================
        # 0. Clear Reading Lists (Fresh Start)
        # ============================================
        if is_logged_in:
            print("\n" + "=" * 60)
            print("STEP 0: Clearing Reading Lists")
            print("=" * 60)
            removed = await reading_list.clear_all_reading_lists()
            total_removed = sum(removed.values())

            print(f"\n>>> Cleared {total_removed} books from reading lists")
            for list_type, count in removed.items():
                print(f"    - {list_type}: {count} removed")

            report.add_step("Clear Reading Lists", "PASS", {
                "removed": removed,
                "total_removed": total_removed
            })

        # ============================================
        # 1. Search Books by Title Under Year
        # ============================================
        print("\n" + "=" * 60)
        print("STEP 1: Search Books by Title Under Year")
        print("=" * 60)

        # Load search queries from test_data.yaml
        search_tests = test_config.get("search_tests", [])

        urls = []
        for search_test in search_tests:
            search_query = search_test.get("query")
            max_year = search_test.get("max_year")
            limit = search_test.get("limit", 5)
            found = await search_books_by_title_under_year(
                search_page=search_page,
                query=search_query,
                max_year=max_year,
                limit=limit
            )
            urls.extend(found)
            print(f"\n>>> Found {len(found)} books for '{search_query}' before {max_year}")

        print(f"\n>>> Total: {len(urls)} books found:")
        for i, url in enumerate(urls, 1):
            print(f"    {i}. {url}")

        report.add_step("Search Books", "PASS" if urls else "WARN", {
            "searches": search_tests,
            "total_found": len(urls),
            "urls": urls
        })

        # ============================================
        # 2. Add Books to Reading List
        # ============================================
        if urls and is_logged_in:
            print("\n" + "=" * 60)
            print("STEP 2: Add Books to Reading List")
            print("=" * 60)

            books_to_add = min(len(urls), 12)  # Add up to 12 books
            actually_added = await add_books_to_reading_list(
                book_page=book_page,
                urls=urls[:books_to_add],
                screenshot_dir=str(SCREENSHOTS_DIR),
                random_seed=42  # Fixed seed for reproducible results
            )

            print(f"\n>>> Added {actually_added} books to reading list (attempted {books_to_add})")
            report.add_step("Add to Reading List", "PASS", {
                "attempted": books_to_add,
                "actually_added": actually_added
            })

            # ============================================
            # 3. Assert Reading List Count
            # ============================================
            print("\n" + "=" * 60)
            print("STEP 3: Verify Reading List Count")
            print("=" * 60)

            expected_count = actually_added
            try:
                await assert_reading_list_count(reading_list, expected_count)
                print(f"\n>>> Assertion PASSED: Found {expected_count} books as expected")
                report.add_step("Verify Reading List", "PASS", {
                    "expected": expected_count,
                    "actual": expected_count
                })
            except AssertionError as e:
                print(f"\n>>> Assertion FAILED: {e}")
                report.add_step("Verify Reading List", "FAIL", {
                    "expected": expected_count,
                    "error": str(e)
                })

        # ============================================
        # 4. Measure Page Performance
        # ============================================
        print("\n" + "=" * 60)
        print("STEP 4: Measure Page Performance")
        print("=" * 60)

        # Load performance thresholds from test_data.yaml
        perf_thresholds = test_config.get("performance_thresholds", {})
        BASE_URL = "https://openlibrary.org"

        performance_tests = []
        for key, config in perf_thresholds.items():
            name = config.get("name", key)
            url = BASE_URL + config.get("url", "")
            threshold = config.get("threshold_ms", 3000)
            performance_tests.append((name, url, threshold))

        print("\n>>> Performance Results:")
        print("-" * 50)

        for name, url, threshold in performance_tests:
            metrics = await measure_page_performance(
                page=page,
                url=url,
                threshold_ms=threshold,
                reporter=perf_reporter
            )

            status = "PASS" if not metrics.get('exceeded') else "WARN"
            load_time = metrics.get('load_time_ms', 'N/A')
            print(f"  {name}: {load_time}ms (threshold: {threshold}ms) [{status}]")

            report.add_step(f"Performance: {name}", status, metrics)

        print("-" * 50)

        # Save performance report
        perf_report_path = perf_reporter.save_report()
        print(f"\n>>> Performance report saved: {perf_report_path}")
        perf_reporter.print_summary()

        # ============================================
        # Generate Final Report
        # ============================================
        print("\n" + "=" * 60)
        print("GENERATING REPORT")
        print("=" * 60)

        report_path = report.save_html_report(REPORTS_DIR / "test_report.html")
        print(f"\n>>> HTML Report saved: {report_path}")

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        report.print_summary()

    except Exception as e:
        print(f"\n>>> ERROR: {e}")
        report.add_step("Error", "FAIL", {"error": str(e)})
        raise

    finally:
        # Cleanup
        await browser.close()
        print("\n>>> Browser closed")
        print("=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
