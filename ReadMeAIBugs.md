# Bugs Found in Code

## Bug 1: Missing await in assert_reading_list_count
```python
actual = reading_list.get_book_count()
```
**Problem**: `get_book_count` is an async function but called without await.
**Fix**:
```python
actual = await reading_list.get_book_count()
```

## Bug 2: int conversion without error handling
```python
year = int(year_text.strip())
```
**Problem**: If the text is not a number (e.g. "First published in 1965"), the code will crash.
**Fix**:
```python
import re
match = re.search(r'\d{4}', year_text)
year = int(match.group()) if match else None
```
**Note**: In our implementation, we used URL parameters for the search (`/search?title=Dune`) instead of parsing year from results, which avoids this issue.

## Bug 3: Browser never closes
```python
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # ... code ...
        # Missing: await browser.close()
```
**Problem**: Browser stays open after execution, leaving zombie processes.
**Fix**: Add `await browser.close()` at the end or use try/finally block.
