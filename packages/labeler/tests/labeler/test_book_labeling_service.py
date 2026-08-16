from database.testing.conftest import temp_db

from labeler.batch_module import BatchItemResult
from labeler.book_labeling_service import BookLabelingService
from database.manager import LabelManager
from database.models import LabelEntry


class TestBookLabelingService:
    def test_process_unlabeled_images_stages_and_locks_correctly(
        self, temp_db, mock_client
    ):
        """Test with mocks that the BookLabelingService correctly stages images, locks them in the database, and submits to xAI."""

        # Set up
        label_manager = LabelManager(temp_db)
        service = BookLabelingService(client=mock_client, label_manager=label_manager)

        test_urls = ["http://img1.jpg", "http://img2.jpg"]

        # Act
        summary = service.process_unlabeled_images(
            batch_name="test_run",
            book_images=test_urls,
            batch_size=2,
            system_prompt="Test prompt",
        )

        # Assert: Inspect the returned Dataclass directly
        assert summary.batch_id == "batch_xyz123"
        assert summary.item_count == 2
        assert summary.staged_items[0].image_url == "http://img1.jpg"

        # Assert: Verify xAI submission occurred
        mock_client.run_batch.assert_called_once()

        # Assert: Check that the database has locked the first two URLs
        entries = (
            temp_db.query(LabelEntry).filter(LabelEntry.image_url.in_(test_urls)).all()
        )
        assert len(entries) == 2
        for entry in entries:
            assert entry.status == "pending"
            assert entry.batch_id == "batch_xyz123"

    def test_update_labels(self, temp_db, mock_client):
        """Test that update_labels fetches results and updates the label table in the database."""

        # Set up
        label_manager = LabelManager(temp_db)
        mock_client.get_batch_results.return_value = [
            # Simulate successful results
            BatchItemResult(
                batch_request_id="item_0",
                response_text="Title 1",
                is_success=True,
            ),
            BatchItemResult(
                batch_request_id="item_1",
                response_text="Title 2",
                is_success=True,
            ),
            # Simulate failed results
            BatchItemResult(
                batch_request_id="item_2",
                response_text="Title 3",
                is_success=False,
            ),
        ]
        service = BookLabelingService(client=mock_client, label_manager=label_manager)

        # Create labels in the database to simulate pending entries
        test_urls = ["http://img1.jpg", "http://img2.jpg", "http://img3.jpg"]

        # Act
        summary = service.process_unlabeled_images(
            batch_name="test_run",
            book_images=test_urls,
            batch_size=3,
            system_prompt="Test prompt",
        )

        # Assert: Check that the database has locked the first two URLs
        entries = (
            temp_db.query(LabelEntry).filter(LabelEntry.image_url.in_(test_urls)).all()
        )
        assert len(entries) == 3
        for entry in entries:
            assert entry.status == "pending"
            assert entry.batch_id == "batch_xyz123"

        # Act
        service.update_labels(batch_id="batch_xyz123")

        # Assert that the database has been updated
        entries = (
            temp_db.query(LabelEntry)
            .filter(LabelEntry.batch_id == "batch_xyz123")
            .all()
        )
        assert len(entries) == 3
        for entry in entries:
            if entry.image_url in ["http://img1.jpg", "http://img2.jpg"]:
                assert entry.status == "completed"
            else:
                assert entry.status == "failed"
