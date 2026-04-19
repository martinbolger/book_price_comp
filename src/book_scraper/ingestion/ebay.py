from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import re


def parse_html(html: str):
    soup = BeautifulSoup(html, "lxml")

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
        price_usd_float = extract_price(price_usd)
        shipping_cost_float = extract_price(shipping_cost)
        total_price = (
            price_usd_float + shipping_cost_float
            if price_usd_float is not None and shipping_cost_float is not None
            else None
        )
        # Get sold date as datetime
        sold_date_dt = pd.to_datetime(extract_sold_date(sold_date))
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
            }
        )
    return books


def extract_sold_date(sold_date_str: str) -> str:
    # Example input: "Sold on Jan 1, 2024"
    match = re.search(r"Sold (.+)", sold_date_str)
    if match:
        return match.group(1)
    return None


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


if __name__ == "__main__":
    data_dir = Path(__file__).parent / "html_output"
    with open(data_dir / "564a95fe9c134.html", "r", encoding="utf-8") as f:
        html = f.read()
    books = parse_html(html)
    print(books)
