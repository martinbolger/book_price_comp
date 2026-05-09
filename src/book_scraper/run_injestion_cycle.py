import asyncio
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth

from book_scraper.seller_info import SellerInfo
from book_scraper.ingestion.main_books import update_db

import random
import logging

logging.basicConfig(filename="scraper.log", level=logging.INFO)
logger = logging.getLogger(__name__)


class Scraper:
    async def run(self, sellers: list[SellerInfo], pagination_check: bool = True):
        """
        Main entry point managing the Playwright lifecycle.

        Parameters
        ----------
        sellers : list[SellerInfo]
            List of seller information objects containing details for scraping.
        pagination_check : bool, optional
            Whether to check for pagination (default is True). If True, the scraper will stop paginating when it finds fewer items than expected,
            which can help avoid unnecessary requests when there are no more new items to scrape.
            Turn this off if you want to scrape all pages regardless of new item count.
        """

        # This is the recommended usage. All pages created will have stealth applied:
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "--no-sandbox",
                ],
            )

            page = await browser.new_page()

            webdriver_status = await page.evaluate("navigator.webdriver")
            print("from new_page: ", webdriver_status)

            for seller in sellers:
                # Set the current URL to the seller's base URL and start pagination loop
                current_url = seller.base_url
                current_page = 1

                # Pagination loop - keep fetching pages until we find fewer items than expected
                while True:
                    try:
                        # Get HTML
                        html = await self.get_page_html(page, current_url)

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
                    items = seller.parser(html, seller.seller_id)

                    # Add items to database
                    added_count = update_db(items)

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

    @staticmethod
    async def human_mouse_move(page):
        # Move the mouse to a few random points on the screen
        for _ in range(3):
            x = random.randint(100, 700)
            y = random.randint(100, 700)
            await page.mouse.move(x, y, steps=random.randint(10, 20))

    async def get_page_html(self, page: Page, url: str, wait_time: int = 30000) -> str:
        page.route("**/*", self.route_intercept)

        # If we are on about:blank, Akamai might be suspicious.
        # Start at a neutral site first.
        if page.url == "about:blank":
            await page.goto("https://www.ebay.com", wait_until="domcontentloaded")

            # # --- MANUAL STEP START ---
            # print("\n[MANUAL INTERVENTION REQUIRED]")
            # print(f"Please solve any CAPTCHAs or navigate to the landing page.")
            # print("Press ENTER in this terminal when you are ready to continue...")

            # # Use run_in_executor so the terminal input doesn't freeze the async loop
            # await asyncio.get_event_loop().run_in_executor(None, input)
            # # --- MANUAL STEP END ---

        async with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
            await self.human_mouse_move(page)  # Move the mouse to mimic human behavior
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
        await page.wait_for_timeout(wait_time)
        return await page.content()


if __name__ == "__main__":
    from book_scraper.seller_info import EbaySellerInfo

    seller_names = [
        # "jnts0710",
        # "beyond_llc_jp01",
        # "ninja_japan_shop",
        # "yoshihiroshop",
        # "nkkt10-26",
        # "japan-nihonbashi",
        # "romando",
        # "moyashi-japan-books",
        # "bookoff.usa.inc",
        # "nature6782"
        # "good_japan"
        # "takarazukadesigns"
        "miccha_485"
    ]
    # Example usage
    sellers = [EbaySellerInfo(seller_id=seller_name) for seller_name in seller_names]

    scraper = Scraper()
    asyncio.run(scraper.run(sellers, pagination_check=True))
