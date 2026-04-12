"""Login Page Object for OpenLibrary authentication."""
import logging
import os
from playwright.async_api import Page
from .base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Page Object for OpenLibrary login page."""

    # Locators
    LOGIN_PATH = "/account/login"
    EMAIL_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    LOGIN_BUTTON = "button[type='submit'], input[type='submit']"
    LOGIN_ERROR = ".note.error, .error-message"
    USER_MENU = ".account-dropdown, [class*='user-menu']"
    LOGGED_IN_INDICATOR = "a[href='/account']"

    def __init__(self, page: Page):
        """Initialize LoginPage."""
        super().__init__(page)

    async def navigate_to_login(self) -> None:
        """Navigate to the login page."""
        await self.navigate(self.LOGIN_PATH)

    async def login(self, email: str, password: str) -> bool:
        """
        Perform login with credentials.

        Args:
            email: User email/username
            password: User password

        Returns:
            True if login successful, False otherwise
        """
        logger.info(f"Attempting login for: {email}")

        await self.navigate_to_login()
        await self.fill_input(self.EMAIL_INPUT, email)
        await self.fill_input(self.PASSWORD_INPUT, password)
        await self.click_element(self.LOGIN_BUTTON)

        await self.page.wait_for_load_state("networkidle")

        # Check if login was successful
        if await self.is_logged_in():
            logger.info("Login successful")
            return True
        else:
            logger.warning("Login failed")
            return False

    async def login_from_env(self) -> bool:
        """
        Login using credentials from environment variables.

        Expects:
            OPENLIBRARY_EMAIL
            OPENLIBRARY_PASSWORD

        Returns:
            True if login successful, False otherwise
        """
        email = os.getenv("OPENLIBRARY_EMAIL")
        password = os.getenv("OPENLIBRARY_PASSWORD")

        if not email or not password:
            logger.error("Missing OPENLIBRARY_EMAIL or OPENLIBRARY_PASSWORD in environment")
            raise ValueError("Login credentials not found in environment variables")

        return await self.login(email, password)

    async def is_logged_in(self) -> bool:
        """Check if user is currently logged in."""
        try:
            # Check for account link or user menu
            account_link = await self.page.query_selector(self.LOGGED_IN_INDICATOR)
            return account_link is not None
        except Exception:
            return False

    async def logout(self) -> None:
        """Logout the current user."""
        await self.navigate("/account/logout")
        await self.page.wait_for_load_state("networkidle")
        logger.info("Logged out successfully")

    async def get_login_error(self) -> str | None:
        """Get login error message if present."""
        try:
            error_el = await self.page.query_selector(self.LOGIN_ERROR)
            if error_el:
                return await error_el.inner_text()
        except Exception:
            pass
        return None
