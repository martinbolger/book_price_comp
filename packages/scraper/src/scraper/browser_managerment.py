import random
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


class PlaywrightFetcherSync:
    """Classs for creating a playwright session and featches HTML."""

    def __init__(self, storage_state_path: str | None = None, headless: bool = False):
        """
        Parameters
        ----------
        storage_state_path : str | None
            The path to a JSON containing the context for the browser.
        headless : bool
            Should the browser open a window? Default, False (no window).
        """
        self.storage_state_path = storage_state_path
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    def __enter__(self):
        """Context manager entry point for the PlaywrightFetcherSync class."""
        # Launch a browser.
        self.playwright = Stealth().use_sync(sync_playwright()).start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)

        # Add context. This could include log in credentials to make scraping
        # without bot blockers posible.
        context_kwargs = {}
        if self.storage_state_path:
            context_kwargs["storage_state"] = self.storage_state_path

        context = self.browser.new_context(**context_kwargs)
        self.page = context.new_page()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point for the PlaywrightFetcherSync class."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_html(self, url: str) -> str | None:
        """Fetches the HTML for a URL."""
        try:
            self.page.goto(url, wait_until="domcontentloaded")

            # Human mimicry delay using standard time.sleep
            delay = random.uniform(3.5, 7.0)
            time.sleep(delay)

            return self.page.content()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None


if __name__ == "__main__":
    with PlaywrightFetcherSync(headless=False) as fetcher:
        html = fetcher.fetch_html("https://shopping.bookoff.co.jp")
        print(f"Retrieved {len(html)} bytes of HTML.")
