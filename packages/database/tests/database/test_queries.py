from datetime import datetime

from database.testing.conftest import temp_db
from database.queries import get_unlabeled_book_images
from database.models import BookEntry, LabelEntry


class TestGetUnlabeledBookImages:
    def test_join_condition(self, temp_db):
        """Test that the join condition correctly identifies unlabeled books."""
        # Add some book entries to the database
        book1 = BookEntry(
            listingid="1",
            image_url="http://example.com/book1.jpg",
            magazine=False,
            sold_date=datetime.strptime("2023-01-01", "%Y-%m-%d"),
        )
        book2 = BookEntry(
            listingid="2",
            image_url="http://example.com/book2.jpg",
            magazine=False,
            sold_date=datetime.strptime("2023-01-02", "%Y-%m-%d"),
        )
        book3 = BookEntry(
            listingid="3",
            image_url="http://example.com/book3.jpg",
            magazine=True,
            sold_date=datetime.strptime("2023-01-02", "%Y-%m-%d"),
        )  # This one is a magazine
        temp_db.add_all([book1, book2, book3])
        temp_db.commit()

        # Add a label entry for book1
        label1 = LabelEntry(
            image_url="http://example.com/book1.jpg", model_used="model_1"
        )
        temp_db.add(label1)
        temp_db.commit()

        # Now, get unlabeled book images
        unlabeled_images = get_unlabeled_book_images(
            model_used="model_1", session=temp_db, target_sellers=None
        )

        # Check that only book2's image URL is returned (book1 is labeled, book3 is a magazine)
        assert "http://example.com/book2.jpg" in unlabeled_images
        assert "http://example.com/book1.jpg" not in unlabeled_images
        assert "http://example.com/book3.jpg" not in unlabeled_images

    def test_target_sellers_filter(self, temp_db):
        """Test that only books from the target sellers are returned."""

        # Add some book entries with different seller_ids
        book1 = BookEntry(
            listingid="1",
            image_url="http://example.com/book1.jpg",
            magazine=False,
            seller_id="seller1",
            sold_date=datetime.strptime("2023-01-02", "%Y-%m-%d"),
        )
        book2 = BookEntry(
            listingid="2",
            image_url="http://example.com/book2.jpg",
            magazine=False,
            seller_id="seller2",
            sold_date=datetime.strptime("2023-01-02", "%Y-%m-%d"),
        )
        temp_db.add_all([book1, book2])
        temp_db.commit()

        # Get unlabeled book images for a specific seller
        unlabeled_images = get_unlabeled_book_images(
            model_used="model_1", session=temp_db, target_sellers=["seller1"]
        )

        # Check that only book1's image URL is returned
        assert "http://example.com/book1.jpg" in unlabeled_images
        assert "http://example.com/book2.jpg" not in unlabeled_images

    def test_order_correct(self, temp_db):
        """Test that books are returned in the correct order based on the sold_date and listingid."""
        book1 = BookEntry(
            listingid="1",
            image_url="http://example.com/book1.jpg",
            magazine=False,
            sold_date=datetime.strptime("2023-01-01", "%Y-%m-%d"),
        )
        book2 = BookEntry(
            listingid="2",
            image_url="http://example.com/book2.jpg",
            magazine=False,
            sold_date=datetime.strptime("2023-01-02", "%Y-%m-%d"),
        )
        book3 = BookEntry(
            listingid="3",
            image_url="http://example.com/book3.jpg",
            magazine=False,
            sold_date=datetime.strptime("2023-01-02", "%Y-%m-%d"),
        )
        temp_db.add_all([book1, book2, book3])
        temp_db.commit()

        # Get unlabeled book images
        unlabeled_images = get_unlabeled_book_images(
            model_used="model_1", session=temp_db, target_sellers=None
        )

        # Check that the images are returned in the correct order (most recent first)
        assert unlabeled_images == [
            "http://example.com/book3.jpg",
            "http://example.com/book2.jpg",
            "http://example.com/book1.jpg",
        ]

    def test_multiple_model_labels(self, temp_db):
        """Test that we can label the same book with different models."""
        book1 = BookEntry(
            listingid="1",
            image_url="http://example.com/book1.jpg",
            magazine=False,
            sold_date=datetime.strptime("2023-01-01", "%Y-%m-%d"),
        )
        temp_db.add_all([book1])
        temp_db.commit()

        label1 = LabelEntry(
            image_url="http://example.com/book1.jpg", model_used="model_1"
        )
        temp_db.add(label1)
        temp_db.commit()

        # Get unlabeled book images with a different model
        unlabeled_images = get_unlabeled_book_images(
            model_used="model_2", session=temp_db, target_sellers=None
        )

        # Check that the same image is returned for a different model
        assert unlabeled_images == [
            "http://example.com/book1.jpg",
        ]

    def test_same_model_labels(self, temp_db):
        """Test that we do not return books that are already labeled with the same model."""
        book1 = BookEntry(
            listingid="1",
            image_url="http://example.com/book1.jpg",
            magazine=False,
            sold_date=datetime.strptime("2023-01-01", "%Y-%m-%d"),
        )
        temp_db.add_all([book1])
        temp_db.commit()

        label1 = LabelEntry(
            image_url="http://example.com/book1.jpg", model_used="model_1"
        )
        temp_db.add(label1)
        temp_db.commit()

        # Get unlabeled book images with a different model
        unlabeled_images = get_unlabeled_book_images(
            model_used="model_1", session=temp_db, target_sellers=None
        )

        # Check that no unlabeled images were returned
        assert unlabeled_images == []
