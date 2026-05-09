import pytest
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from book_scraper.ingestion.manager import ManifestManager, BookManager
from book_scraper.models import ManifestEntry, BookEntry
from book_scraper.database import init_db, get_engine


@pytest.fixture
def temp_db():
    # Initialize the database and create a session
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)

    session = sessionmaker(bind=engine)
    session = session()

    yield session

    session.close()


class TestManifestManager:
    def test_url_covered(self, temp_db):
        manager = ManifestManager(temp_db, expiration_days=7)
        url = "https://example.com"

        # URL not covered
        assert not manager.url_covered(url)
        # Add URL to manifest
        manager.add_to_manifest(url)
        # URL is covered
        assert manager.url_covered(url)

    def test_add_to_manifest(self, temp_db):
        current_time = datetime(2024, 5, 15, 10, 30)
        manager = ManifestManager(temp_db, expiration_days=7, current_time=current_time)
        url = "https://example.com"

        # Add URL to manifest
        manager.add_to_manifest(url, last_read_date=current_time)

        # Check if URL is in manifest
        entry = temp_db.query(ManifestEntry).filter(ManifestEntry.url == url).first()
        assert entry is not None
        assert entry.url == url

        # Try to add the same URL again with the same date (should not update)
        manager.add_to_manifest(url, last_read_date=current_time)

        # Check if URL is still in manifest and not duplicated
        entries = temp_db.query(ManifestEntry).filter(ManifestEntry.url == url).all()
        assert len(entries) == 1

    def test_url_not_covered_expired(self, temp_db):
        manager = ManifestManager(temp_db, expiration_days=1)
        url = "https://example.com"

        # Set expired date
        expired_date = datetime.now() - timedelta(days=10)

        # Add URL with expired date
        manager.add_to_manifest(url, last_read_date=expired_date)

        # URL should not be covered
        assert not manager.url_covered(url)

        # Update URL with current date
        manager.add_to_manifest(url, last_read_date=datetime.now())

        # URL should now be covered
        assert manager.url_covered(url)


class TestBookManager:
    def test_add_book(self, temp_db):
        manager = BookManager(temp_db)
        book_data = {
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

        # Add book to database
        manager.add_book(**book_data)

        # Check if book is in database
        book = (
            temp_db.query(BookEntry)
            .filter(BookEntry.listingid == book_data["listingid"])
            .first()
        )
        assert book is not None
        assert book.title == book_data["title"]
        assert book.seller_id == book_data["seller_id"]

    def test_add_seller_id(self, temp_db):
        manager = BookManager(temp_db)
        book_data = {
            "listingid": "12345",
            "title": "Test Book",
            "magazine": False,
            "sold_date": datetime(2024, 5, 15),
            "image_url": "https://example.com/image.jpg",
            "price_usd": 10.0,
            "shipping_cost": 2.0,
            "total_price": 12.0,
        }

        # Add book to database
        result = manager.add_book(**book_data)

        # Book added
        assert result is True
        assert book_data["listingid"] is not None

        # Add seller ID to book
        seller_id = "correct_seller_id"
        manager.add_seller_id(book_data["listingid"], seller_id)

        # Check if seller_id is correctly set
        book = (
            temp_db.query(BookEntry)
            .filter(BookEntry.listingid == book_data["listingid"])
            .first()
        )
        assert book is not None
        assert book.seller_id == seller_id

    def test_add_image_file(self, temp_db):
        manager = BookManager(temp_db)
        book_data_list = [
            {
                "listingid": "12345",
                "title": "Test Book",
                "magazine": False,
                "sold_date": datetime(2024, 5, 15),
                "image_url": "https://example.com/image.jpg",
                "price_usd": 10.0,
                "shipping_cost": 2.0,
                "total_price": 12.0,
            },
            {
                "listingid": "12346",
                "title": "Test Book 2",
                "magazine": False,
                "sold_date": datetime(2024, 5, 15),
                "image_url": "https://example.com/image.jpg",
                "price_usd": 20.0,
                "shipping_cost": 2.0,
                "total_price": 12.0,
            },
        ]

        # Add books to database
        for book_data in book_data_list:
            manager.add_book(**book_data)

        # Add image file path
        image_file_path = "/path/to/image.jpg"
        manager.add_image_file(book_data["image_url"], image_file_path)

        # Check if image file path is updated in database for all
        # books with the same image URL
        for book_data in book_data_list:
            book = (
                temp_db.query(BookEntry)
                .filter(BookEntry.listingid == book_data["listingid"])
                .first()
            )
            assert book is not None
            assert book.image_file == image_file_path
