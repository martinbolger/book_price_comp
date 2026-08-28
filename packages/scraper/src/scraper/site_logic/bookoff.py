from bs4 import BeautifulSoup, Tag
import re
from scraper.site_logic.strategy import ScraperStrategy


class BookOffStrategy(ScraperStrategy):
    def __init__(self, search_term: str):
        self.search_term = search_term

    @property
    def current_url(self) -> str:
        """Returns the starting URL for a specific search term."""
        return f"https://shopping.bookoff.co.jp/search/keyword/{self.search_term}"

    def parse(self, html: str):
        """Parse HTML for a Book Off search page."""
        soup = BeautifulSoup(html, "html.parser")
        listings = soup.select(".productItem")
        return [self._parse_listing(listing, identifier = self.search_term) for listing in listings] if listings else []

    def should_continue(self, **kwargs) -> bool:
        """There is no next page for Book Off search results, so this always returns False."""
        return False

    @staticmethod
    def _get_first_result(soup: BeautifulSoup):
        """Get the first item from a book off search."""
        return soup.select_one(".productItem")

    @staticmethod
    def _get_text(item: Tag, selector: str) -> str | None:
        """Extract stripped text from a CSS selector within an item node."""
        node = item.select_one(selector)
        return node.get_text(strip=True) if node else None

    def _parse_listing(self, item: Tag, identifier: str) -> dict:
        """Extract all raw fields from a single search result container into a dictionary."""
        text_fields = {
            "raw_title": ".productItem__title",
            "raw_author": ".productItem__author",
            "raw_price": ".productItem__price",
            "raw_date": ".productItem__date",
            "raw_item_genre": ".productItem__genreItem",
        }

        # Extract all text fields via mapping
        record = {
            key: self._get_text(item, selector) for key, selector in text_fields.items()
        }

        # Extract attribute fields (e.g. href)
        link_tag = item.select_one("a.productItem__link")
        record["raw_rel_url"] = link_tag.get("href") if link_tag else None
        id_tag = item.select_one("[data-item]")
        record["raw_item_id"] = id_tag.get("data-item") if id_tag else None

        # Add identifier to the record
        record["search_term"] = identifier

        return record


if __name__ == "__main__":
    from pathlib import Path

    base_path = Path(__file__).parent
    print(str(base_path))
    with open(base_path / "bookoff_test.html") as f:
        html = f.read()
    bookoffstrat = BookOffStrategy("search term")
    print(bookoffstrat.parse(html))
    print(bookoffstrat.current_url)
