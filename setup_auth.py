"""
Setup Authentication for OpenLibrary
Run this script once to save your login session.
"""
import asyncio
from playwright.async_api import async_playwright

AUTH_STATE_PATH = "auth_state.json"


async def setup_auth():
    print("=" * 50)
    print("OpenLibrary Authentication Setup")
    print("=" * 50)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to login page
        await page.goto("https://openlibrary.org/account/login")

        print("\n1. Login manually in the browser window")
        print("2. After successful login, press ENTER here...")
        input()

        # Save the authentication state
        await context.storage_state(path=AUTH_STATE_PATH)
        print(f"\nAuth state saved to: {AUTH_STATE_PATH}")

        await browser.close()
        print("Done! You can now run: python main.py")


if __name__ == "__main__":
    asyncio.run(setup_auth())
