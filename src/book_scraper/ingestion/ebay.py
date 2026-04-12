from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import re


def parse_data(html: str):
    soup = BeautifulSoup(html, "lxml")

    # Step 1: Isolate the results section
    results_container = soup.select_one("ul.srp-results")

    # Find the img tag with the specific class
    listings = results_container.select("li.s-card")

    rows = []
    for listing in listings:
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
        rows.append(
            {
                "title": title,
                "sold_date": extract_sold_date(sold_date),
                "image_url": image_url,
                "price_usd": extract_price(price_usd),
                "shipping_cost": extract_price(shipping_cost),
            }
        )
    # Create dataframe
    book_data = pd.DataFrame(
        rows, columns=["title", "sold_date", "image_url", "price_usd", "shipping_cost"]
    )
    # Calculate total price
    book_data["total_price_usd"] = book_data["price_usd"] + book_data["shipping_cost"]
    # Convert sold_date to datetime
    book_data["sold_date"] = pd.to_datetime(book_data["sold_date"])
    book_data.to_csv("ebay_books.csv", index=False)


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
    data_dir = Path(__file__).parent.parent.parent / "data"
    with open(data_dir / "d40fcb34f8fcc.html", "r", encoding="utf-8") as f:
        html = f.read()
    parse_data(html)
