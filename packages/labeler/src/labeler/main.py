from datetime import datetime, timezone
from unittest.mock import MagicMock

from database.queries import get_unlabeled_book_images
from database.main import get_session
from labeler.batch_module import Batch


def create_batch_name(seller_id: str):
    """Create batch name using the seller ID and current timestamp."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{seller_id}_{timestamp}"


def main(seller_id: str, batch_size: int = 10, client=None):
    # Get images to label from the database
    session = get_session()
    book_images = get_unlabeled_book_images(session, target_sellers=[seller_id])

    print(f"Found {len(book_images)} unlabeled images for seller '{seller_id}'.")

    # Create a batch
    batch_name = create_batch_name(seller_id)
    batch = Batch(
        name=batch_name,
        system_prompt="""You are a precise Japanese book title extractor.

Extract the complete Japanese title from the book cover image.

Guidelines:
- Capture the full title, including any series name, main title, and volume number if present.
- When there is both a series name (often vertical or smaller) and a large main title, combine them naturally (e.g. "ホラークリエイターズファイル 視禍").
- Prefer the most complete and accurate reading of all prominent Japanese text on the cover.
- Include volume indicators (第X巻, Vol.X, etc.) when clearly visible.
- Only use web_search if critical parts of the title are illegible or the structure is highly ambiguous. If you search, make exactly one call.
- Output format: Return ONLY the Japanese title (and volume if applicable). No English, no explanations, no author names.

Examples of good output:
本のタイトル (vol 4)""",
        batch_size=batch_size,
        client=client,
    )

    # Add images to the batch
    batch.add_images_to_batch(book_images)

    print(
        f"Batch '{batch_name}' created with {len(batch.batch_requests)} images for seller '{seller_id}'."
    )
    for image in batch.batch_requests:
        print(f"Added image to batch: {image}")

    # Run the batch with the XAI SDK
    batch.run_batch()


if __name__ == "__main__":
    # main(
    #     seller_id="moyashi-japan-books", batch_size=5, client=MagicMock()
    # )  # Replace MagicMock with actual XAI SDK client if available
    main(
        seller_id="moyashi-japan-books", batch_size=5
    )  # Replace MagicMock with actual XAI SDK client if available
