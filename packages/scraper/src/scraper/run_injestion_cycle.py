import asyncio
import os
import boto3
import tempfile
from datetime import datetime
import random
import logging
from typing import Literal
from pathlib import Path

from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth
from sqlalchemy.orm import sessionmaker

from database.database import init_db, get_engine
from database.manager import BookManager

from scraper.seller_info import SellerInfo
from scraper.seller_info import EbaySellerInfo

logging.basicConfig(filename="scraper.log", level=logging.DEBUG)
logger = logging.getLogger(__name__)

s3_client = boto3.client("s3")


class Scraper:
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
            browser = await p.chromium.launch(
                # headless=False
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-zygote",
                ],
            )

            page = await browser.new_page()

            webdriver_status = await page.evaluate("navigator.webdriver")

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
                        # Save a screenshot of the page
                        await self.save_page_screenshot(
                            page=page,
                            step_name=f"{seller.seller_id}_page{current_page}",
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

                    # Update current page
                    current_url = seller.get_next_page_url(current_page)
                    current_page += 1

            await browser.close()
            logger.debug(
                f"Completed scrape of the following sellers: {", ".join([s.seller_id for s in sellers])}."
            )

    @staticmethod
    async def human_mouse_move(page):
        # Move the mouse to a few random points on the screen
        for _ in range(3):
            x = random.randint(100, 700)
            y = random.randint(100, 700)
            await page.mouse.move(x, y, steps=random.randint(10, 20))

    async def get_page_html(self, page: Page, url: str, wait_time: int = 8000) -> str:
        # page.route("**/*", self.route_intercept)

        # If we are on about:blank, Akamai might be suspicious.
        # Start at a neutral site first.
        if page.url == "about:blank":
            landing_page = "https://www.ebay.com"
            logger.debug(
                f"Detected initial launch; opening landing page: {landing_page}."
            )
            await page.goto(landing_page, wait_until="domcontentloaded")

            # # --- MANUAL STEP START ---
            # print("\n[MANUAL INTERVENTION REQUIRED]")
            # print(f"Please solve any CAPTCHAs or navigate to the landing page.")
            # print("Press ENTER in this terminal when you are ready to continue...")

            # # Use run_in_executor so the terminal input doesn't freeze the async loop
            # await asyncio.get_event_loop().run_in_executor(None, input)
            # # --- MANUAL STEP END ---

        async with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
            # await self.human_mouse_move(page)  # Move the mouse to mimic human behavior
            # Trigger the click via JS with an internal delay
            await page.evaluate(f"""
                setTimeout(() => {{
                    const a = document.createElement('a');
                    a.href = '{url}';
                    document.body.appendChild(a);
                    a.click();
                }}, {random.randint(500, 1500)}); 
            """)

        # Wait for the content to settle
        logger.debug("Awaiting page load...")
        await page.wait_for_timeout(wait_time)
        logger.debug("Awaiting page content...")
        return await page.content()

    async def save_page_screenshot(self, page: Page, step_name: str):
        """
        Save a screenshot of the page for debugging when running in headless mode.

        Params
        ------
        page:
            Playwright page object.
        step_name:
            Name of the step in the scraping process. This can include
            the name of the seller and page.
        """
        # Create path to local location where screenshot can be saved
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create the path to the screenshot file. Make sure
        # the directory exists first.
        if not self.screenshot_path.exists():
            self.screenshot_path.mkdir(parents=True)
        local_path = self.screenshot_path / f"{step_name}_{timestamp}.png"

        # 1. Take the screenshot locally
        await page.screenshot(path=local_path, full_page=False)

        # If we are running on AWS, upload to S3 bucket
        if self.run_location == "aws":
            s3_key = f"screenshots/{timestamp}_{step_name}.png"
            s3_client.upload_file(local_path, self.screenshot_bucket, s3_key)
            logger.debug(
                f"Screenshot saved to S3: s3://{self.screenshot_bucket}/{s3_key}"
            )

            # 3. Clean up the local path to keep Lambda memory lean
            os.remove(local_path)


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


def _configure_screenshot_storage(self):
    """Sets up the attributes for the location for storing screenshots"""
    if self.run_location == "aws":
        self.screenshot_bucket = os.environ["SCREENSHOT_BUCKET"]
        self.screenshot_path = "/tmp"
    elif self.run_location == "local":

        # Use environment variable to determine location to store
        # screenshots if it exists
        screenshot_path = os.environ.get("LOCAL_SCREENSHOT_PATH")

        if screenshot_path:
            # If the env var was set, keep the screenshots so
            # that they can be used for debugging.
            self.screenshot_path = Path(screenshot_path)
            self.clear_screenshots = False


if __name__ == "__main__":

    seller_names = [
        # "jnts0710",
        # "beyond_llc_jp01",
        # "ninja_japan_shop",
        # "yoshihiroshop",
        # "nkkt10-26",
        # "japan-nihonbashi",
        "romando",
        # "moyashi-japan-books",
        # "bookoff.usa.inc",
        # "nature6782",
        # "good_japan",
        # "takarazukadesigns",
        # "miccha_485"
    ]
    # Example usage
    sellers = [EbaySellerInfo(seller_id=seller_name) for seller_name in seller_names]

    scraper = Scraper(run_location="local", screenshot_path="/app/screenshots")
    asyncio.run(scraper.run(sellers, pagination_check=True))
