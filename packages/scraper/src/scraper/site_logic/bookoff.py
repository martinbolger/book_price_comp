from bs4 import BeautifulSoup, Tag


def build_search_url(search_term: str):
    """Get the base URL for the given search term."""
    return f"https://shopping.bookoff.co.jp/search/keyword/{search_term}"


def get_first_result(soup: BeautifulSoup):
    """Get the first item from a book off search."""
    return soup.select_one(".productItem")


def _get_text(item: Tag, selector: str) -> str | None:
    """Extract stripped text from a CSS selector within an item node."""
    node = item.select_one(selector)
    return node.get_text(strip=True) if node else None


def parse_item(item: Tag) -> dict:
    """Extract all raw fields from a single search result container into a dictionary."""
    text_fields = {
        "raw_title": ".productItem__title",
        "raw_author": ".productItem__author",
        "raw_price": ".productItem__price",
        "raw_date": ".productItem__date",
    }

    # Extract all text fields via mapping
    record = {key: _get_text(item, selector) for key, selector in text_fields.items()}

    # Extract attribute fields (e.g. href)
    link_tag = item.select_one("a.productItem__link")
    record["raw_rel_url"] = link_tag.get("href") if link_tag else None

    return record


if __name__ == "__main__":
    from pathlib import Path

    base_path = Path(__file__).parent
    print(str(base_path))
    with open(base_path / "bookoff_test.html") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    first_result = get_first_result(soup)
    print(parse_item(first_result))
