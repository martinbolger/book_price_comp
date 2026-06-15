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
