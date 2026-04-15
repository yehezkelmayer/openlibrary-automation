# OpenLibrary Automation Test Suite

Automated E2E testing framework for OpenLibrary.org using Playwright and Python.

## Project Structure

```
openlibrary_automation/
├── main.py                  # Main entry point
├── setup_auth.py            # Manual authentication setup
├── .env                     # Environment config (credentials)
├── data/
│   └── test_data.yaml       # Test data (searches, thresholds)
├── pages/
│   ├── base_page.py         # Base Page Object class
│   ├── search_page.py       # Search page POM
│   ├── book_page.py         # Book page POM
│   └── reading_list_page.py # Reading list POM
├── helpers/
│   ├── browser.py           # Browser singleton
│   └── report_generator.py  # HTML report generator
├── utils/
│   ├── data_loader.py       # YAML data loader
│   ├── performance_reporter.py  # Performance metrics & history
│   └── test_functions.py    # Core test functions
├── screenshots/             # Test screenshots
├── reports/                 # HTML & performance reports
├── requirements.txt         # Dependencies
└── README.md
```

## Architecture

### Design Patterns

- **Page Object Model (POM)**: Each page has a dedicated class with locators and methods
- **Data-Driven Testing**: Test data loaded from `data/test_data.yaml`
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

```bash
# Browser settings
BASE_URL=https://openlibrary.org
HEADLESS=true
TIMEOUT=30000

# OpenLibrary Login Credentials (required for full functionality)
OL_EMAIL=your_email@example.com
OL_PASSWORD=your_password
```

## Authentication Setup

### Option 1: Auto-Login with .env (Recommended)

The simplest way - just add your OpenLibrary credentials to the `.env` file:

1. Create an OpenLibrary account at: https://openlibrary.org/account/create
2. Edit the `.env` file with your credentials:
   ```bash
   OL_EMAIL=your_email@example.com
   OL_PASSWORD=your_password
   ```
3. Run the tests - login happens automatically!

The session will be saved to `auth_state.json` for future runs.

### Option 2: Manual Login (if CAPTCHA appears)

If OpenLibrary shows CAPTCHA, use manual login:

```bash
python setup_auth.py
```

This will:

1. Open a browser window
2. Navigate to OpenLibrary login page
3. Wait for you to login manually (complete any CAPTCHA)
4. Save the session to `auth_state.json`

## Running Tests

```bash
# 1. Configure credentials in .env file (one-time setup)
#    Edit .env and set OL_EMAIL and OL_PASSWORD

# 2. Run the tests
python main.py

# Run with visible browser (for debugging)
HEADLESS=false python main.py
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
- Saves to performance history

## Reports

### HTML Report

Generated automatically at `reports/test_report.html` with:

- Test step status (PASS/WARN/FAIL)
- Step details with visualizations
- Screenshots gallery
- Summary statistics

### Performance Reports

Generated in `reports/performance/` directory:

```
reports/performance/
├── summary.json           # Aggregated statistics
├── run_20260415_130732.json
├── run_20260415_140000.json
└── ...                    # Up to 50 runs kept
```

Each run file contains:
```json
{
  "run_id": "20260415_130732",
  "measurements": [...],
  "summary": {
    "avg_load_time_ms": 1500,
    "thresholds_exceeded": 1
  }
}
```

## Limitations

1. **Login Required**: Adding books to reading list requires OpenLibrary account
2. **Rate Limiting**: OpenLibrary may rate-limit requests
3. **Dynamic Selectors**: Some selectors may change over time
4. **Year Extraction**: Publication year parsing depends on page structure

## Performance Thresholds

| Page         | Threshold |
| ------------ | --------- |
| Search Page  | 3000ms    |
| Book Page    | 2500ms    |
| Reading List | 2000ms    |

## Dependencies

- Python 3.10+
- Playwright 1.49+
- PyYAML 6.0+
