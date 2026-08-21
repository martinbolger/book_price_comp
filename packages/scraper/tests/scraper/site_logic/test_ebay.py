from bs4 import BeautifulSoup

from scraper.site_logic.ebay import EbayStrategy

LISTING_HTML = """
<li class="s-card" data-listingid="123456789012">
    <div class="s-card__image-wrapper">
        <img class="s-card__image" src="https://i.ebayimg.com/images/g/abc/s-l500.webp" />
    </div>
    <div class="s-card__title">
        <span class="primary">Attack on Titan Vol. 1-10 Manga Set Japanese</span>
    </div>
    <div class="s-card__price">$45.99</div>
    <div class="s-card__attribute-row">
        <span class="secondary">+$5.00 delivery</span>
    </div>
    <div class="s-card__attribute-row">
        <span class="secondary">Free returns</span>
    </div>
    <div class="s-card__caption">Sold Jan 1, 2024</div>
</li>
"""


def test_parse_listing_extracts_expected_fields():
    strategy = EbayStrategy(seller_id="moyashi-japan-books")
    listing = BeautifulSoup(LISTING_HTML, "lxml").select_one("li.s-card")

    record = strategy.parse_listings(listing)

    assert record["listingid"] == "123456789012"
    assert record["raw_title"] == "Attack on Titan Vol. 1-10 Manga Set Japanese"
    assert record["raw_price"] == "$45.99"
    assert record["raw_sold_date"] == "Sold Jan 1, 2024"
    assert record["image_url"] == "https://i.ebayimg.com/images/g/abc/s-l500.webp"
    assert record["raw_attributes"] == [
        {"text": "+$5.00 delivery", "classes": ["secondary"]},
        {"text": "Free returns", "classes": ["secondary"]},
    ]
