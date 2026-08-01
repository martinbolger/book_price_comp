from datetime import datetime, timedelta
from freezegun import freeze_time

from database.manager import ManifestManager, BookManager, LabelManager
from database.models import ManifestEntry, BookEntry, LabelEntry


class TestManifestManager:
    def test_seller_id_covered(self, temp_db):
        manager = ManifestManager(temp_db, expiration_days=7)
        seller_id = "https://example.com"

        # seller_id not covered
        assert not manager.seller_id_covered(seller_id)
        # Add seller_id to manifest
        manager.add_to_manifest(seller_id)
        # seller_id is covered
        assert manager.seller_id_covered(seller_id)

    def test_add_to_manifest(self, temp_db):
        current_time = datetime(2024, 5, 15, 10, 30)
        manager = ManifestManager(temp_db, expiration_days=7, current_time=current_time)
        seller_id = "https://example.com"

        # Add seller_id to manifest
        manager.add_to_manifest(seller_id, last_read_date=current_time)

        # Check if seller_id is in manifest
        entry = (
            temp_db.query(ManifestEntry)
            .filter(ManifestEntry.seller_id == seller_id)
            .first()
        )
        assert entry is not None
        assert entry.seller_id == seller_id

        # Try to add the same seller_id again with the same date (should not update)
        manager.add_to_manifest(seller_id, last_read_date=current_time)

        # Check if seller_id is still in manifest and not duplicated
        entries = (
            temp_db.query(ManifestEntry)
            .filter(ManifestEntry.seller_id == seller_id)
            .all()
        )
        assert len(entries) == 1

    def test_seller_id_not_covered_expired(self, temp_db):
        manager = ManifestManager(temp_db, expiration_days=1)
        seller_id = "example_seller_id"

        # Set expired date
        expired_date = datetime.now() - timedelta(days=10)

        # Add seller_id with expired date
        manager.add_to_manifest(seller_id, last_read_date=expired_date)

        # seller_id should not be covered
        assert not manager.seller_id_covered(seller_id)

        # Update seller_id with current date
        manager.add_to_manifest(seller_id, last_read_date=datetime.now())

        # seller_id should now be covered
        assert manager.seller_id_covered(seller_id)


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


class TestLabelManager:
    @freeze_time("2026-01-01 12:00:00")
    def test_add_new_url(self, temp_db):
        manager = LabelManager(temp_db)
        image_url = "https://example.com/image.jpg"
        model_used = "grok-4.3"
        batch_request_id = "batch_123"

        manager.add_new_url(image_url, model_used, batch_request_id)

        entry = (
            temp_db.query(LabelEntry).filter(LabelEntry.image_url == image_url).first()
        )
        assert entry is not None
        assert entry.image_url == image_url
        assert entry.model_used == model_used
        assert entry.batch_request_id == batch_request_id
        assert entry.created_at == datetime(2026, 1, 1, 12, 0, 0)
        assert entry.updated_at == datetime(2026, 1, 1, 12, 0, 0)

    def test_update_url_label(self, temp_db):
        manager = LabelManager(temp_db)
        image_url = "https://example.com/image.jpg"
        model_used = "grok-4.3"
        batch_request_id = "batch_123"
        label = "Test Label"

        # Add a new URL first
        manager.add_new_url(image_url, model_used, batch_request_id)

        # Update the label for the URL
        manager.update_url_label(image_url, model_used, label)

        entry = (
            temp_db.query(LabelEntry).filter(LabelEntry.image_url == image_url).first()
        )
        assert entry is not None
        assert entry.label == label
        assert entry.status == "completed"

    # TODO: Add test for update_urls_to_failed method.
