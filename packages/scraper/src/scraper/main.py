from scraper.browser_managerment import PlaywrightFetcherSync
from scraper.site_logic.strategy import ScraperStrategy
from database.listing_manager import RawListingManager, RawEbayListingManager, RawBookoffListingManager
from scraper.site_logic.bookoff import BookOffStrategy
from scraper.site_logic.ebay import EbayStrategy
from database.main import get_session

def scrape_url(
    fetcher: PlaywrightFetcherSync,
    site_strategy: ScraperStrategy,
    listing_manager: RawListingManager,
) -> str | None:
    """Run the scraper for a given URL."""
    html = fetcher.fetch_html(site_strategy.current_url)
    parsed_data = site_strategy.parse(html)
    added_count = listing_manager.add_listings(parsed_data)
    return added_count, html



def orchestrate_ebay(
    seller_ids: list[str],
    storage_state_path: str = "/app/ebay_state.json",
    headless: bool = False,
    results_per_page: int = 240,
    database_url: str|None = None,
) -> str | None:
    """Run the scraper for a given URL."""
    fetcher = PlaywrightFetcherSync(storage_state_path=storage_state_path, headless=headless)
    session = get_session(url=database_url)
    listing_manager = RawEbayListingManager(session=session)

    # Start playwright fetcher and listing manager context
    with fetcher as fetcher, listing_manager as manager:
        for seller_id in seller_ids:
            site_strategy = EbayStrategy(seller_id=seller_id, results_per_page=results_per_page)
            # Scrape all pages for the current seller
            while True:
                added_count, html = scrape_url(
                    fetcher=fetcher,
                    site_strategy=site_strategy,
                    listing_manager=manager,
                )
                if not site_strategy.should_continue(html=html, added_count=added_count):
                    break

def orchestrate_bookoff(
    search_terms: list[str],
    headless: bool = False,
    database_url: str|None = None,
) -> str | None:
    """Run the scraper for a given URL."""
    fetcher = PlaywrightFetcherSync(headless=headless)
    session = get_session(url=database_url)
    listing_manager = RawBookoffListingManager(session=session)
    with fetcher as fetcher, listing_manager as manager:
        for search_term in search_terms:
            site_strategy = BookOffStrategy(search_term=search_term)
            scrape_url(
                fetcher=fetcher,
                site_strategy=site_strategy,
                listing_manager=manager,
            )


# if __name__ == "__main__":
#     database_url = "sqlite:///book_arbitrage.db"

#     orchestrate_bookoff(
#         search_terms=["ただ制服を着てるだけ", "砂の女"],
#         headless=False,
#         database_url=database_url,
#     )
#     print("Scraping completed.")

#     # Print entries from the database
#     from database.models import RawBookoffListing

#     session = get_session(url=database_url)
#     entries = session.query(RawBookoffListing).all()
#     for entry in entries:
#         print(entry.search_term, entry.created_at, entry.raw_item_id, entry.raw_title, entry.raw_price, entry.raw_date)


if __name__ == "__main__":
    database_url = "sqlite:///book_arbitrage.db"

    orchestrate_ebay(
        seller_ids=["ninja_japan_shop", "moyashi-japan-books"],
        headless=False,
        database_url=database_url,
    )

    print("Scraping completed.")

    # Print entries from the database
    from database.models import RawEbayListing

    session = get_session(url=database_url)
    entries = session.query(RawEbayListing).all()
    for entry in entries:
        print(entry.created_at, entry.listingid, entry.raw_title, entry.raw_price, entry.raw_sold_date)
