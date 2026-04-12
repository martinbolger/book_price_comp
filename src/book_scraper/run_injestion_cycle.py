from pathlib import Path

from playwright.sync_api import sync_playwright, Page
import hashlib


class Scraper:
    @staticmethod
    def hash_string(string: str, hash_length: int = 13) -> str:
        """Hashes a string using SHA-256 and returns the first `hash_length` characters of the hex digest."""
        return hashlib.sha256(string.encode("utf-8")).hexdigest()[:hash_length]

    def write_html_to_file(self, html: str, output_path: Path) -> None:
        """Writes HTML content to a file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def run(self, urls: list[str], output_path: Path):
        """Main entry point managing the Playwright lifecycle."""

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(user_agent="Mozilla/5.0")
            page = context.new_page()

            for url in urls:
                # Get HTML
                html = self.get_page_html(page, url)
                # Hash URL to create unique filename
                url_hash = self.hash_string(url)
                # Write HTML to file
                self.write_html_to_file(html, output_path / f"{url_hash}.html")

                # Parse items in HTML
                # For each item:
                #   If book is in data, stop parsing further items on the page (assuming new items are added at the end of the page)
                #   else, if book is not in data, continue parsing items on the page until we find a book that is in the data or we run out of items on the page
                # If no existing data was found, continue to next page of URL if possible
                # If different,
                #   save new HTML and update manifest

            browser.close()

    def get_page_html(self, page: Page, url: str, wait_time: int = 3000) -> str:
        """Pure logic for fetching."""
        page.goto(url, timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(wait_time)
        return page.content()
