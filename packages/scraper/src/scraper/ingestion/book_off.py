from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from pathlib import Path
import json


def fetch_bookoff_html(isbn: str):
    url = f"https://shopping.bookoff.co.jp/search/keyword/{isbn}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # set False to watch it
        page = browser.new_page()

        page.goto(url, timeout=60000)

        # wait for content to load
        page.wait_for_timeout(3000)

        html = page.content()

        browser.close()

        return html


def get_book_data(isbn: str, data_dir: Path) -> str:
    html_file = data_dir / f"{isbn}.html"

    # Load from file.
    if (html_file).exists():
        with open(html_file, "r", encoding="utf8") as file:
            html = file.read()
    # Scrape
    else:
        html = fetch_bookoff_html(isbn)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html


from bs4 import BeautifulSoup


def parse_book(html: str, isbn: str):
    soup = BeautifulSoup(html, "lxml")

    item = soup.select_one(".productItem")
    if not item:
        return None

    # Title
    title_el = item.select_one(".productItem__title")
    title = title_el.text.strip() if title_el else None

    # Author
    author_el = item.select_one(".productItem__author")
    author = author_el.text.strip() if author_el else None

    # Price
    price_el = item.select_one(".productItem__price")
    price = None
    if price_el:
        raw_price = price_el.text.strip()
        # Extract numeric part
        raw_price = raw_price.split("円")[0]
        raw_price = raw_price.replace("¥", "").replace(",", "")
        try:
            price = int(raw_price)
        except:
            price = None

    # Condition (中古 etc.)
    condition_el = item.select_one(".tag")
    condition = condition_el.text.strip() if condition_el else None

    # Stock
    stock_el = item.select_one(".productItem__stock")
    stock = stock_el.text.strip() if stock_el else None

    return {
        "isbn": isbn,
        "title": title,
        "author": author,
        "price": price,
        "currency": "JPY",
        "condition": condition,
        "stock": stock,
        "source": "bookoff",
    }


if __name__ == "__main__":
    jan = "9784001141276"
    data = Path(__file__).parent.parent.parent / "data"
    html = get_book_data(jan, data)

    data = parse_book(html, jan)
    # Convert Python object to a pretty-printed JSON string with 4-space indentation
    pretty_json_string = json.dumps(data, indent=4, ensure_ascii=False)
    print(pretty_json_string)
