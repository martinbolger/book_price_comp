from freezegun import freeze_time
from unittest.mock import MagicMock
from database.testing.conftest import temp_db

from database.manager import LabelManager, BookManager
from database.models import BookEntry, LabelEntry

from labeler.batch_module import XAI_Batch
from labeler.main import create_batch_name, main


@freeze_time("2026-01-01 12:00:00")
def test_create_batch_name_format():
    """Verify batch name contains seller ID and expected timestamp format."""
    name = create_batch_name("seller_42")
    assert name.startswith("seller_42_")
    # Length check for seller_42_YYYYMMDD_HHMMSS
    assert len(name) == len("seller_42_20260101_120000")


def test_database_locks_correctly(temp_db, mock_client):
    """Test that the BookLabelingService correctly locks URLs in the database so that they are not relabeled on a subsequent call."""
    # Arrange
    label_manager = LabelManager(temp_db)
    book_manager = BookManager(temp_db)

    # Add books to the database for testing
    book_data = [
        {
            "listingid": "book3",
            "title": "book3",
            "image_url": "http://img3.jpg",
            "seller_id": "test_seller",
        },
        {
            "listingid": "book2",
            "title": "book2",
            "image_url": "http://img2.jpg",
            "seller_id": "test_seller",
        },
        {
            "listingid": "book1",
            "title": "book1",
            "image_url": "http://img1.jpg",
            "seller_id": "test_seller",
        },
    ]
    for book in book_data:
        book_manager.add_book(**book)

    assert temp_db.query(BookEntry).count() == 3

    # Act
    summary = main(
        seller_id="test_seller",
        batch_size=2,
        client=mock_client,
        label_manager=label_manager,
        session=temp_db,
    )

    print(summary)

    # Execute and fetch all rows
    entries = temp_db.query(LabelEntry).all()

    # Print each entry
    for entry in entries:
        # __dict__ extracts the attributes as a dictionary for clean printing
        print(entry.__dict__)

    # Assert: Check that the database has locked the first two URLs
    entries = (
        temp_db.query(LabelEntry)
        .filter(LabelEntry.image_url.in_([book["image_url"] for book in book_data[:2]]))
        .all()
    )
    assert len(entries) == 2
    for entry in entries:
        assert entry.status == "pending"
        assert entry.batch_id == "batch_xyz123"

    # Act
    summary = main(
        seller_id="test_seller",
        batch_size=2,
        client=mock_client,
        label_manager=label_manager,
        session=temp_db,
    )

    # Assert that the third URL is now staged.
    assert len(summary.staged_items) == 1
    assert summary.staged_items[0].image_url == "http://img1.jpg"

    entries = (
        temp_db.query(LabelEntry)
        .filter(LabelEntry.image_url == "http://img1.jpg")
        .all()
    )
    assert len(entries) == 1
    assert entries[0].status == "pending"
    assert entries[0].batch_id == "batch_xyz123"
