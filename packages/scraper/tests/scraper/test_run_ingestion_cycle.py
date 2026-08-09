import asyncio
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from database.database import init_db
from database.models import BookEntry
from scraper.run_injestion_cycle import update_db, Scraper
from scraper.seller_info import SellerInfo


@pytest.fixture
def temp_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    monkeypatch.setattr("scraper.run_injestion_cycle.get_engine", lambda: engine)
    return engine


def test_update_db_adds_book_with_correct_seller_id(temp_db):
    books = [
        {
            "listingid": "12345",
            "title": "Test Book",
            "magazine": False,
            "sold_date": datetime(2024, 5, 15),
            "image_url": "https://example.com/image.jpg",
            "price_usd": 10.0,
            "shipping_cost": 2.0,
            "total_price": 12.0,
            "seller_id": "my_seller",
        }
    ]

    added_count = update_db(books)

    assert added_count == 1

    session = sessionmaker(bind=temp_db)()
    book = session.query(BookEntry).filter(BookEntry.listingid == "12345").first()

    assert book is not None
    assert book.seller_id == "my_seller"
    session.close()


def test_looks_like_results_page_accepts_s_item_markup():
    html = "<html><body><ul class='srp-results'><li class='s-item'></li></ul></body></html>"

    assert Scraper.looks_like_results_page(html)


def test_looks_like_blocked_page_detects_human_verification():
    html = "<html><body><h1>Verify you are human</h1></body></html>"

    assert Scraper.looks_like_blocked_page(html)
    assert not Scraper.looks_like_results_page(html)


def test_wait_for_human_verification_reloads_page(monkeypatch):
    class DummyPage:
        def __init__(self):
            self.reloaded = False

        async def reload(self, **kwargs):
            self.reloaded = True

    page = DummyPage()
    calls = []

    async def fake_to_thread(func, *args, **kwargs):
        calls.append((func, args, kwargs))
        return None

    monkeypatch.setattr("scraper.run_injestion_cycle.asyncio.to_thread", fake_to_thread)

    async def run_test():
        scraper = Scraper(run_location="local")
        await scraper.wait_for_human_verification(page, "https://example.com")

    asyncio.run(run_test())

    assert page.reloaded is True
    assert calls
