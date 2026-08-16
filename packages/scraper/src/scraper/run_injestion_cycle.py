import asyncio
import os
import tempfile
import random
import logging
from typing import Literal
from pathlib import Path

from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth
from sqlalchemy.orm import sessionmaker

from database.main import init_db, get_engine
from database.manager import BookManager

from scraper.seller_info import SellerInfo
from scraper.seller_info import EbaySellerInfo

logging.basicConfig(filename="scraper.log", level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Scraper:
    @staticmethod
    def looks_like_results_page(html: str) -> bool:
        if not html:
            return False

        lowered = html.lower()
        if "verify you are human" in lowered or "captcha" in lowered:
            return False

        if "srp-results" in lowered or "s-item" in lowered or "s-card" in lowered:
            return True

        return False

    @staticmethod
    def looks_like_blocked_page(html: str) -> bool:
        if not html:
            return False

        lowered = html.lower()
        if "verify you are human" in lowered or "captcha" in lowered:
            return True

        return False

    def __init__(
        self,
        run_location: Literal["local", "aws"],
        screenshot_path: Path = None,
        screenshot_bucket: str = "",
    ):
        self.run_location = run_location
        if screenshot_path:
            self.screenshot_path = Path(screenshot_path)
        else:
            local_temp_dir = tempfile.TemporaryDirectory(
                prefix="screenshot_", delete=True
            )
            self.screenshot_path = Path(local_temp_dir.name)
        self.screenshot_bucket = screenshot_bucket

    async def run(self, sellers: list[SellerInfo], pagination_check: bool = True):
        """
        Main entry point managing the Playwright lifecycle.

        Parameters
        ----------
        sellers : list[SellerInfo]
            List of seller information objects containing details for scraping.
        pagination_check : bool, optional
            Whether to check for pagination (default is True). If True, the scraper will stop
            paginating when it finds fewer items than expected,
            which can help avoid unnecessary requests when there are no more new items to scrape.
            Turn this off if you want to scrape all pages regardless of new item count.
        """

        # This is the recommended usage. All pages created will have stealth applied:
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=False)

            context = await browser.new_context(storage_state="ebay_state.json")
            page = await context.new_page()

            webdriver_status = await page.evaluate("navigator.webdriver")

            await self.warmup_session(page)

            for seller in sellers:
                # Set the current URL to the seller's base URL and start pagination loop
                current_url = seller.base_url
                current_page = 1

                # Pagination loop - keep fetching pages until we find fewer items than expected
                while True:
                    try:
                        # Get HTML
                        logger.debug(
                            f"Getting HTML for page {current_page} of seller {seller}..."
                        )
                        html = await self.get_page_html(page, current_url)
                        logger.debug(
                            f"Received HTML for page {current_page} of seller {seller}."
                        )

                    except Exception as e:
                        # If this fails, log the error and break out of the pagination loop for this seller
                        logger.error(
                            f"Error fetching page {current_page} for seller {seller.seller_id}: {e}"
                        )
                        break

                    # If HTML was not returned, log a warning and break out of the pagination loop for this seller
                    if not html:
                        logger.warning(
                            f"No HTML content retrieved for page {current_page} of seller {seller.seller_id}. Stopping pagination."
                        )
                        break

                    # Parse items from HTML
                    logger.debug(
                        f"Parsing HTML for page {current_page} of seller {seller}..."
                    )
                    items = seller.parser(html, seller.seller_id)
                    logger.debug(
                        f"Parsed HTML for page {current_page} of seller {seller}."
                    )

                    # Add items to database
                    logger.debug(
                        f"Updating database for content parsed from page {current_page} of seller {seller}..."
                    )
                    added_count = update_db(items)
                    logger.debug(
                        f"Updated database for content parsed from page {current_page} of seller {seller}."
                    )

                    # If we found fewer items than expected, we have reached the end of new items for this seller.
                    # If there is no next page, we will also stop.
                    if (
                        pagination_check and added_count != seller.results_per_page
                    ) or not seller.has_next_page(html):
                        print(
                            f"Found {added_count} new items on page {current_page} for seller {seller.seller_id}. Stopping pagination."
                        )
                        break
                    else:
                        print(
                            f"Found {added_count} new items on page {current_page} for seller {seller.seller_id}. Fetching next page..."
                        )

                    # Before navigating to next_page_url
                    delay = random.uniform(3.5, 7.0)
                    logger.debug(f"Sleeping {delay:.2f}s to mimic human browsing...")
                    await page.wait_for_timeout(int(delay * 1000))
                    current_url = seller.get_next_page_url(current_page)
                    current_page += 1

            await browser.close()
            logger.debug(
                f"Completed scrape of the following sellers: {', '.join([s.seller_id for s in sellers])}."
            )

    async def warmup_session(self, page: Page):
        logger.debug("Warming up session on eBay homepage...")
        await page.goto(
            "https://www.ebay.com", wait_until="domcontentloaded", timeout=60000
        )
        # Give JS tracking scripts time to execute and store session cookies
        await page.wait_for_timeout(random.randint(2500, 4500))

    async def get_page_html(self, page: Page, url: str) -> str:
        logger.debug(f"Waiting for search results to load for URL: {url}...")

        for attempt in range(3):
            try:
                # Replaced time.sleep with non-blocking asyncio.sleep
                await asyncio.sleep(random.uniform(5.0, 10.0))
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                html = await page.content()

                if self.looks_like_results_page(html):
                    return html

                if self.looks_like_blocked_page(html):
                    logger.warning(
                        "Bot challenge detected! Please solve the CAPTCHA in the browser."
                    )

                    # Pause the script and wait for user input in the terminal
                    input(
                        "--> Press ENTER here in the terminal once you've solved it..."
                    )

                    # Refresh HTML after you solve the challenge
                    html = await page.content()
                    if self.looks_like_results_page(html):
                        return html

                await page.wait_for_timeout(2000)

            except Exception as exc:
                if attempt == 2:
                    logger.error(
                        "Timed out waiting for search results. Possibly blocked by security check."
                    )
                    raise
                logger.warning(
                    f"Attempt {attempt + 1} failed while loading {url}: {exc}. Retrying..."
                )

        raise RuntimeError(f"Unable to load search results for {url}")


def update_db(books: list[dict]) -> int:
    """
    Updates the database with the given list of book data dictionaries.

    Returns
    -------
    int
        The number of new book entries added to the database.
    """
    # STEP 1: Ensure the database and tables exist
    engine = get_engine()
    init_db(engine)

    session = sessionmaker(bind=engine)
    session_local = session()
    added_count = 0

    # STEP 2: Open a communication session
    # Using 'with' ensures the session closes automatically when done
    with session_local as session:

        # STEP 3: Hand that session to your Manager
        book_manager = BookManager(session)

        # STEP 4: Add books to the database
        for book in books:
            added = book_manager.add_book(**book)
            book_manager.add_seller_id(book["listingid"], book["seller_id"])
            if added:
                added_count += 1
    return added_count


async def start_scraping(event):
    # Extract data from the Lambda 'event' (passed via curl or trigger)
    # e.g., curl -d '{"sellers": ["jnts0710"]}'
    seller_names = event.get("sellers", [])

    sellers = [EbaySellerInfo(seller_id=name) for name in seller_names]

    run_location = "aws"
    screenshot_bucket = os.environ.get("SCREENSHOT_BUCKET")
    screenshot_path = "/tmp"

    scraper = Scraper(run_location=run_location, screenshot_path=screenshot_path)
    # If your scraper returns data, you can capture it here
    result = await scraper.run(sellers, pagination_check=True)
    return result


def handler(event, context):
    """This is the entry point Lambda looks for"""
    return asyncio.run(start_scraping(event))


if __name__ == "__main__":

    seller_names = [
        # "jnts0710",
        # "beyond_llc_jp01",
        # "ninja_japan_shop",
        # "yoshihiroshop",
        # "nkkt10-26",
        # "japan-nihonbashi",
        # "romando",
        "moyashi-japan-books",
        # "bookoff.usa.inc",
        # "nature6782",
        # "good_japan",
        # "takarazukadesigns",
        # "miccha_485",
    ]
    # Example usage
    sellers = [EbaySellerInfo(seller_id=seller_name) for seller_name in seller_names]

    scraper = Scraper(run_location="local", screenshot_path="/app/screenshots")
    asyncio.run(scraper.run(sellers, pagination_check=True))
