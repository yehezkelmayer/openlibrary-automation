"""Data-Driven Tests using external test data files."""
import pytest
import allure
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.test_functions import search_books_by_title_under_year
from utils.data_loader import DataLoader

# Load test data
data_loader = DataLoader(Path(__file__).parent.parent / "data")
search_test_data = data_loader.get_search_test_data()


@allure.epic("OpenLibrary Automation")
@allure.feature("Data-Driven Tests")
class TestDataDrivenSearch:
    """Data-driven test suite using external test data."""

    @allure.story("Parameterized search tests")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "test_case",
        search_test_data,
        ids=[tc["id"] for tc in search_test_data]
    )
    async def test_search_from_data_file(self, page, test_case):
        """
        Data-driven search test.

        Test data is loaded from data/test_data.yaml
        """
        query = test_case["query"]
        max_year = test_case["max_year"]
        limit = test_case["limit"]
        description = test_case["description"]

        allure.dynamic.title(description)
        allure.dynamic.description(
            f"Query: {query}\n"
            f"Max Year: {max_year}\n"
            f"Limit: {limit}"
        )

        with allure.step(f"Execute search: {query}"):
            urls = await search_books_by_title_under_year(
                page=page,
                query=query,
                max_year=max_year,
                limit=limit
            )

        with allure.step("Validate results"):
            allure.attach(
                f"Found {len(urls)} results:\n" + "\n".join(urls),
                name="Search Results",
                attachment_type=allure.attachment_type.TEXT
            )

            # Verify we got a valid response (list)
            assert isinstance(urls, list), "Expected list of URLs"

            # Verify limit is respected
            assert len(urls) <= limit, \
                f"Expected at most {limit} results, got {len(urls)}"


@allure.epic("OpenLibrary Automation")
@allure.feature("Data-Driven Tests")
class TestPerformanceDataDriven:
    """Data-driven performance tests."""

    @pytest.fixture
    def perf_thresholds(self):
        """Load performance thresholds from data file."""
        return data_loader.get_performance_thresholds()

    @allure.story("Performance thresholds from config")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.performance
    async def test_performance_from_config(self, page, perf_thresholds):
        """Test performance using thresholds from config file."""
        from utils.test_functions import measure_page_performance
        from utils.performance_reporter import PerformanceReporter

        reporter = PerformanceReporter(
            Path(__file__).parent.parent / "performance_report.json"
        )

        for page_name, config in perf_thresholds.items():
            url = config["url"]
            threshold = config["threshold_ms"]
            name = config["name"]

            with allure.step(f"Measure {name}"):
                full_url = f"https://openlibrary.org{url}" if url.startswith("/") else url

                metrics = await measure_page_performance(
                    page=page,
                    url=full_url,
                    threshold_ms=threshold,
                    reporter=reporter
                )

                allure.attach(
                    str(metrics),
                    name=f"{name} Metrics",
                    attachment_type=allure.attachment_type.JSON
                )

        # Save report
        reporter.save_report()
