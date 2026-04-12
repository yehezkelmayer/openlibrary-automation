# OpenLibrary Automation Test Suite

Automated E2E testing framework for OpenLibrary.org using Playwright and Python.

## Project Structure

```
openlibrary_automation/
├── main.py                  # Main entry point
├── setup_auth.py            # Authentication setup script
├── config/
│   └── config.yaml          # Configuration settings
├── data/
│   ├── test_data.yaml       # Test data (YAML)
│   └── test_data.json       # Test data (JSON)
├── pages/
│   ├── __init__.py
│   ├── base_page.py         # Base Page Object class
│   ├── search_page.py       # Search page POM
│   ├── book_page.py         # Book page POM
│   └── reading_list_page.py # Reading list POM
├── helpers/
│   ├── browser.py           # Browser singleton
│   └── report_generator.py  # HTML report generator
├── utils/
│   ├── __init__.py
│   ├── data_loader.py       # YAML/JSON data loader
│   ├── logger.py            # Logging configuration
│   ├── performance_reporter.py  # Performance metrics
│   └── test_functions.py    # Core test functions
├── screenshots/             # Test screenshots
├── reports/                 # HTML & JSON reports
├── conftest.py              # Pytest fixtures (optional)
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Dependencies
└── README.md
```

## Architecture

### Design Patterns
- **Page Object Model (POM)**: Each page has a dedicated class with locators and methods
- **Data-Driven Testing**: Test data loaded from external YAML/JSON files
- **Single Responsibility Principle**: Utilities separated by function

### Key Components
1. **BasePage**: Common functionality (navigation, screenshots, performance)
2. **SearchPage**: Book search with year filtering and pagination
3. **BookPage**: Individual book operations (add to reading list)
4. **ReadingListPage**: Reading list validation

## Installation

```bash
# Clone the repository
cd openlibrary_automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Configuration

### Environment Variables (.env)
```
BASE_URL=https://openlibrary.org
HEADLESS=true
TIMEOUT=30000
```

### Config File (config/config.yaml)
```yaml
browser:
  headless: true
  timeout: 30000

performance_thresholds:
  search_page_ms: 3000
  book_page_ms: 2500
  reading_list_ms: 2000
```

## Authentication Setup (Required)

OpenLibrary uses CAPTCHA on login. To bypass this, run the setup script once:

```bash
python setup_auth.py
```

This will:
1. Open a browser window
2. Navigate to OpenLibrary login page
3. Wait for you to login manually (complete any CAPTCHA)
4. Save the session to `auth_state.json`

After setup, the automation will use the saved session.

## Running Tests

### Run Main Test Suite
```bash
# Run with visible browser
HEADLESS=false python main.py

# Run headless (default)
python main.py
```

### Run with pytest (optional)
```bash
pytest tests/
```

### Run with Allure Reports
```bash
pytest --alluredir=reports/allure-results
allure serve reports/allure-results
```

## Test Functions

### 1. search_books_by_title_under_year
```python
async def search_books_by_title_under_year(
    page: Page,
    query: str,
    max_year: int,
    limit: int = 5
) -> list[str]
```
- Searches for books by title
- Filters by publication year
- Supports pagination
- Returns list of book URLs

### 2. add_books_to_reading_list
```python
async def add_books_to_reading_list(
    page: Page,
    urls: list[str],
    screenshot_dir: str = "screenshots"
) -> None
```
- Navigates to each book URL
- Adds to "Want to Read" or "Already Read" (random)
- Takes screenshot for each book

### 3. assert_reading_list_count
```python
async def assert_reading_list_count(
    page: Page,
    expected_count: int
) -> None
```
- Opens reading list page
- Counts books
- Asserts against expected count

### 4. measure_page_performance
```python
async def measure_page_performance(
    page: Page,
    url: str,
    threshold_ms: int
) -> dict
```
- Measures load_time_ms, dom_content_loaded_ms, first_paint_ms
- Logs warning if threshold exceeded
- Generates performance_report.json

## Reports

### HTML Report
Generated automatically at `reports/test_report.html` with:
- Test step status (PASS/WARN/FAIL)
- Step details
- Summary statistics

### Performance Report
Generated at `reports/performance_report.json` with format:
```json
{
  "generated_at": "2024-01-01T12:00:00",
  "measurements": [...],
  "summary": {
    "avg_load_time_ms": 1500,
    "max_load_time_ms": 2500
  }
}
```

## Limitations

1. **Login Required**: Adding books to reading list requires OpenLibrary account
2. **Rate Limiting**: OpenLibrary may rate-limit requests
3. **Dynamic Selectors**: Some selectors may change over time
4. **Year Extraction**: Publication year parsing depends on page structure

## Performance Thresholds

| Page | Threshold |
|------|-----------|
| Search Page | 3000ms |
| Book Page | 2500ms |
| Reading List | 2000ms |

## Dependencies

- Python 3.10+
- Playwright 1.49+
- pytest 8.3+
- allure-pytest 2.13+
- PyYAML 6.0+
