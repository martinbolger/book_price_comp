from bs4 import BeautifulSoup
from dataclasses import dataclass
import re
import pandas as pd


@dataclass
class SellerInfo:
    seller_id: str
    results_per_page: int

    @property
    def base_url(self):
        raise NotImplementedError("Subclasses must implement the base_url property")

    def has_next_page(self, html_content: str) -> bool:
        """Determines if there is a next page based on the HTML content."""
        raise NotImplementedError("Subclasses must implement the has_next_page method")

    def get_next_page_url(self, current_page: int) -> str:
        """Returns the URL for the next page based on the current page number."""
        raise NotImplementedError(
            "Subclasses must implement the get_next_page_url method"
        )

    def parser(self, html_content: str) -> list[dict]:
        """Parses the HTML content and returns a list of dictionaries containing book data."""
        raise NotImplementedError("Subclasses must implement the parser method")


@dataclass
class EbaySellerInfo(SellerInfo):
    results_per_page: int = 240

    @property
    def base_url(self):
        return f"https://www.ebay.com/sch/i.html?LH_Complete=1&LH_Sold=1&_fss=1&_saslop=1&_sasl={self.seller_id}&LH_SpecificSeller=1&_ipg={self.results_per_page}"

    def has_next_page(self, html_content: str) -> bool:
        """Determines if there is a next page based on the HTML content."""

        soup = BeautifulSoup(html_content, "lxml")

        # Step 1: Isolate the results section
        next_button = soup.select_one("a.pagination__next")

        if next_button and next_button["href"] is not None:
            return True
        else:
            return False

    def get_next_page_url(self, current_page: int) -> str:
        return f"{self.base_url}&_pgn={current_page + 1}"

    def parser(self, html_content: str, seller_id: str):
        """Parse HTML for an Ebay sold page."""
        soup = BeautifulSoup(html_content, "lxml")

        # Step 1: Isolate the results section
        results_container = soup.select_one("ul.srp-results")

        # Find the img tag with the specific class
        listings = results_container.select("li.s-card")

        books = []
        for listing in listings:
            listingid = listing.get("data-listingid")
            img_tag = listing.select_one(".s-card__image")
            title_tag = listing.select_one(".s-card__title .primary")
            price_tag = listing.select_one(".s-card__price")
            attribute_rows = listing.select(".s-card__attribute-row .secondary")
            sold_date = listing.select_one(".s-card__caption")

            # Title
            title = title_tag.get_text(strip=True)
            # Sold date
            sold_date = sold_date.get_text(strip=True)
            # Image URL
            image_url = img_tag.get("src")
            # Price
            price_usd = price_tag.get_text(strip=True)
            # Shipping
            for row in attribute_rows:
                text = row.get_text(strip=True)
                if "$" in text or "delivery" in text.lower():
                    shipping_cost = text
                    break

            # Get price and shipping as floats for total price calculation
            price_usd_float = self.extract_price(price_usd)
            shipping_cost_float = self.extract_price(shipping_cost)
            total_price = (
                price_usd_float + shipping_cost_float
                if price_usd_float is not None and shipping_cost_float is not None
                else None
            )
            # Get sold date as datetime
            sold_date_dt = pd.to_datetime(self.extract_sold_date(sold_date))
            books.append(
                {
                    "listingid": listingid,
                    "title": title,
                    "magazine": "magazine" in title.lower(),
                    "sold_date": sold_date_dt,
                    "image_url": image_url,
                    "price_usd": price_usd_float,
                    "shipping_cost": shipping_cost_float,
                    "total_price": total_price,
                    "seller_id": seller_id,
                }
            )
        return books

    @staticmethod
    def extract_sold_date(sold_date_str: str) -> str:
        # Example input: "Sold on Jan 1, 2024"
        match = re.search(r"Sold (.+)", sold_date_str)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def extract_price(price_str: str) -> float:
        # Remove any non-numeric characters except for the decimal point
        cleaned_price = re.sub(r"[^\d.]", "", price_str).strip()
        try:
            if cleaned_price:
                return float(cleaned_price)
            else:
                return 0.0
        except ValueError:
            return None
