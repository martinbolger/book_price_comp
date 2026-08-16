from database.listing_manager import RawBookoffListingManager, RawEbayListingManager
from database.models import RawBookoffListing, RawEbayListing
from database.testing.conftest import temp_db


class TestRawEbayListingManager:
    def test_add_listing(self, temp_db):
        manager = RawEbayListingManager(temp_db)

        result = manager._add_listing(
            listingid="ebay_123",
            raw_title="Test eBay title",
            raw_price="$12.99",
            raw_sold_date="2026-01-01",
            image_url="https://example.com/cover.jpg",
            raw_attributes=[
                {"text": "+$5.00 delivery", "classes": ["secondary"]},
                {"text": "Free returns", "classes": ["secondary"]},
            ],
        )

        assert result is True

        entry = (
            temp_db.query(RawEbayListing)
            .filter(RawEbayListing.listingid == "ebay_123")
            .first()
        )
        assert entry is not None
        assert entry.raw_title == "Test eBay title"
        assert entry.raw_attributes == [
            {"text": "+$5.00 delivery", "classes": ["secondary"]},
            {"text": "Free returns", "classes": ["secondary"]},
        ]

    def test_add_listing_duplicate(self, temp_db):
        manager = RawEbayListingManager(temp_db)

        manager._add_listing(
            listingid="ebay_123",
            raw_title="Test eBay title",
            raw_price="$12.99",
            raw_sold_date="2026-01-01",
            image_url="https://example.com/cover.jpg",
            raw_attributes="{}",
        )
        result = manager._add_listing(
            listingid="ebay_123",
            raw_title="Duplicate title",
            raw_price="$20.00",
            raw_sold_date="2026-01-02",
            image_url="https://example.com/cover-2.jpg",
            raw_attributes="{}",
        )

        assert result is False


class TestRawBookoffListingManager:
    def test_add_listing(self, temp_db):
        manager = RawBookoffListingManager(temp_db)

        result = manager._add_listing(
            raw_item_id="0015580570",
            raw_rel_url="/used/0015580570",
            raw_title="BookOff Title",
            raw_author="BookOff Author",
            raw_price="1100円",
            raw_date="2026/01/01",
        )

        assert result is True

        entry = (
            temp_db.query(RawBookoffListing)
            .filter(RawBookoffListing.raw_item_id == "0015580570")
            .first()
        )
        assert entry is not None
        assert entry.raw_rel_url == "/used/0015580570"
        assert entry.raw_title == "BookOff Title"
        assert entry.raw_author == "BookOff Author"
        assert entry.raw_price == "1100円"
        assert entry.raw_date == "2026/01/01"

    def test_add_listing_duplicate(self, temp_db):
        manager = RawBookoffListingManager(temp_db)

        manager._add_listing(
            raw_item_id="0015580570",
            raw_rel_url="/used/0015580570",
            raw_title="BookOff Title",
            raw_author="BookOff Author",
            raw_price="1100円",
            raw_date="2026/01/01",
        )
        result = manager._add_listing(
            raw_item_id="0015580570",
            raw_rel_url="/used/0015580570",
            raw_title="Updated Title",
            raw_author="Updated Author",
            raw_price="999円",
            raw_date="2026/01/02",
        )

        assert result is False
