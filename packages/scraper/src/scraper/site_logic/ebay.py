from bs4 import BeautifulSoup

from scraper.site_logic.strategy import ScraperStrategy


class EbayStrategy(ScraperStrategy):
    def __init__(self, seller_id: str, results_per_page: int = 100):
        self.seller_id = seller_id
        self.results_per_page = results_per_page
        self.current_page = 1
        self.pagination_check = True

    @property
    def current_url(self) -> str:
        return (
            f"https://www.ebay.com/sch/i.html?"
            f"LH_Complete=1&LH_Sold=1&_fss=1&_saslop=1&_sasl={self.seller_id}"
            f"&LH_SpecificSeller=1&_ipg={self.results_per_page}"
            f"&_pgn={self.current_page}"
        )

    def parse(self, html: str) -> list[dict]:
        """Parse HTML for an eBay search page."""
        soup = BeautifulSoup(html, "lxml")

        # Step 1: Isolate the results section
        results_container = soup.select_one("ul.srp-results")

        # Find the img tag with the specific class
        listings = results_container.select("li.s-card")

        return [self._parse_listing(listing, identifier = self.seller_id) for listing in listings] if listings else []

    def _get_image_url(self, listing) -> str:
        img_tag = listing.select_one(".s-card__image")
        return img_tag.get("src") if img_tag else None

    def _parse_listing(self, listing, identifier: str) -> dict:
        text_fields = {
            "raw_title": ".s-card__title .primary",
            "raw_price": ".s-card__price",
            "raw_sold_date": ".s-card__caption",
        }

        # Add text fields to the record dictionary
        record = {
            key: self._get_text(listing, value) for key, value in text_fields.items()
        }

        # Add additional fields to the record dictionary
        record["listingid"] = listing.get("data-listingid")
        record["image_url"] = self._get_image_url(listing)
        attribute_nodes = listing.select(".s-card__attribute-row .secondary")
        # Get the text and classes for each attribute node and store them in a list of dictionaries
        # The classes can help us interpret the meaning of the attribute
        # (e.g., if it is a price and the class says it has a strikethrough, that was the original price before a discount)
        record["raw_attributes"] = [
            {
                "text": node.get_text(strip=True),
                "classes": node.get("class", []),
            }
            for node in attribute_nodes
            if node.get_text(strip=True)
        ]

        # Add identifier to the record
        record["seller_id"] = identifier

        return record

    def should_continue(self, **kwargs):
        """Check for a next page link. If all of the listings on the current page were added and there is a next page, return True."""
        added_count = kwargs.get("added_count", 0)
        html = kwargs.get("html", "")
        if (
            self.pagination_check and added_count != self.results_per_page
        ) or not self._has_next_page(html):
            return False
        else:
            # Go to the next page
            self.current_page += 1
            return True

    @staticmethod
    def _has_next_page(html: str) -> bool:
        """Determines if there is a next page based on the HTML content."""

        soup = BeautifulSoup(html, "lxml")

        # Step 1: Isolate the results section
        next_button = soup.select_one("a.pagination__next")

        if next_button and next_button["href"] is not None:
            return True
        else:
            return False


if __name__ == "__main__":

    from pathlib import Path

    base_path = Path(__file__).parent
    ebay_strat = EbayStrategy(seller_id="moyashi-japan-books")
    print(ebay_strat.current_url)
    with open(base_path / "ebay_test.html") as f:
        html = f.read()
    print(ebay_strat.parse(html))
