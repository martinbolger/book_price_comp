from playwright.sync_api import sync_playwright
import hashlib
import csv

from pathlib import Path


# Conver url to hash.
# If hash is already in the manifest, confirm the url matches the hash.
# If it doesn't, add a digit to the hash and check again until we find a match or an empty slot.
# If it does, we already have the HTML.
# If the HTML doesn't exist, we can fetch it and save it to the filename in the manifest.


def fetch_html(url: str):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60000)

        # wait for content to load
        page.wait_for_timeout(3000)

        html = page.content()

        browser.close()

        return html


def get_book_data(url: str, data_dir: Path) -> str:

    html_filename = hash_string(url) + ".html"
    html_file = data_dir / html_filename

    # Load from file.
    if (html_file).exists():
        with open(html_file, "r", encoding="utf8") as file:
            html = file.read()
    # Scrape
    else:
        data_dir.parent.mkdir(parents=True, exist_ok=True)
        html = fetch_html(url)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html


def hash_string(string: str, hash_length: int = 13) -> str:
    """Hashes a string using SHA-256 and returns the first `hash_length` characters of the hex digest."""
    return hashlib.sha256(string.encode("utf-8")).hexdigest()[:hash_length]


if __name__ == "__main__":
    seller_name = "example_seller"
    sold_url = f"https://www.ebay.com/sch/i.html?_ex_kw=set%2C+magazine&_sacat=267&LH_Complete=1&LH_Sold=1&_fss=1&_saslop=1&_sasl=+{seller_name}&LH_SpecificSeller=1&_ipg=240"
    data_dir = Path(__file__).parent.parent.parent / "data"
    html = get_book_data(sold_url, data_dir)
