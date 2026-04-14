"""
OpenLibrary Automation - Main Entry Point
Run with: python main.py
"""
import asyncio
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

# Configuration
AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
REPORTS_DIR = Path(__file__).parent / "reports"


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
    report = ReportGenerator()
    perf_reporter = PerformanceReporter(REPORTS_DIR / "performance_report.json")

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
        print(f"\n>>> Logged in: {is_logged_in}")

        if not is_logged_in:
            print(">>> WARNING: Not logged in. Run 'python save_auth_manually.py' first.")
            print(">>> Continuing with limited functionality...\n")

        # ============================================
        # 0. Clear Reading Lists (Fresh Start)
        # ============================================
        if is_logged_in:
            print("\n" + "=" * 60)
            print("STEP 0: Clearing Reading Lists")
            print("=" * 60)

            reading_list = ReadingListPage(page)
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

        # Multiple search queries for variety
        searches = [
            ("Dune", 1985, 5),
            ("Foundation", 1970, 4),
            ("1984", 1950, 3),
            ("Brave New World", 1940, 3),
        ]

        urls = []
        for search_query, max_year, limit in searches:
            found = await search_books_by_title_under_year(
                page=page,
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
            "searches": [{"query": q, "max_year": y, "limit": l} for q, y, l in searches],
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
                page=page,
                urls=urls[:books_to_add],
                screenshot_dir=str(SCREENSHOTS_DIR)
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
                await assert_reading_list_count(page, expected_count)
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

        performance_tests = [
            ("Search Page", "https://openlibrary.org/search?q=python", 3000),
            ("Book Page", "https://openlibrary.org/works/OL45883W", 2500),
            ("Reading List", "https://openlibrary.org/account/books/want-to-read", 2000),
        ]

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
