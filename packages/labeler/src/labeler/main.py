from datetime import datetime, timezone

from database.queries import get_unlabeled_book_images
from labeler.book_labeling_service import BookLabelingService
from labeler.batch_module import Label_Batch
from database.manager import LabelManager


def create_batch_name(seller_id: str):
    """Create batch name using the seller ID and current timestamp."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{seller_id}_{timestamp}"


def main(
    seller_id: str,
    batch_size: int = 10,
    client=None,
    label_manager=None,
    session=None,
):
    """Main function to orchestrate the labeling of book images for a given seller."""

    # Get unlabeled book images for the specified seller
    book_images = get_unlabeled_book_images(
        model_used=client.model, target_sellers=[seller_id], session=session
    )

    # Create a labeling service with the provided client and label manager
    book_labeling_service = BookLabelingService(
        client=client, label_manager=label_manager
    )

    # Run labeling service for the unlabeled images
    summary = book_labeling_service.process_unlabeled_images(
        batch_name=create_batch_name(seller_id),
        book_images=book_images,
        batch_size=batch_size,
        system_prompt="""You are a precise Japanese book title extractor.

                        Extract the complete Japanese title from the book cover image.

                        Guidelines:
                        - Capture the full title, including any series name, main title, and volume number if present.
                        - When there is both a series name (often vertical or smaller) and a large main title, combine them naturally (e.g. "ホラークリエイターズファイル 視禍").
                        - Prefer the most complete and accurate reading of all prominent Japanese text on the cover.
                        - Include volume indicators (第X巻, Vol.X, etc.) when clearly visible.
                        - Only use web_search if critical parts of the title are illegible or the structure is highly ambiguous. If you search, make exactly one call.
                        - Output format: Return ONLY the Japanese title (and volume if applicable). No English, no explanations, no author names.

                        Examples of good output: 本のタイトル (vol 4)
    """,
    )

    return summary


def sync_completed_batches(
    client: Label_Batch,
    label_manager: LabelManager,
) -> dict[str, int]:
    """Orchestrates checking all pending batches in the DB and updating their labels."""
    service = BookLabelingService(client=client, label_manager=label_manager)

    # 1. Fetch pending batch IDs from DB
    pending_batch_ids = label_manager.get_pending_batch_ids()

    summary = {}
    # 2. Iterate and update each batch
    for batch_id in pending_batch_ids:
        try:
            items_updated = service.update_labels(batch_id)
            summary[batch_id] = items_updated
        except Exception as e:
            # Prevent one bad/unfinished batch from stopping the entire loop
            print(f"Failed to sync batch {batch_id}: {e}")
            summary[batch_id] = 0

    return summary


if __name__ == "__main__":
    from labeler.batch_module import XAI_Batch
    from database.main import get_session
    from database.manager import LabelManager
    from unittest.mock import create_autospec

    # Create a mock client with the real batch information.
    # mock_client = create_autospec(XAI_Batch, isnstance=True)
    # mock_client.create_batch.return_value = "batch_3ca9c1bd-e781-421f-9931-6703649c9959"
    # mock_client.run_batch.return_value = None
    # mock_client.model = "grok-4.3"

    session = get_session()
    label_manager = LabelManager(session=session)

    xai_client = XAI_Batch()

    # main(
    #     seller_id="moyashi-japan-books",
    #     batch_size=5,
    #     client=xai_client,
    #     label_manager=label_manager,
    #     session=session,
    # )

    # Sync labels
    result = sync_completed_batches(client=xai_client, label_manager=label_manager)
    print(result)
