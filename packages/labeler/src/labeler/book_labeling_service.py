from labeler.batch_module import Label_Batch
from database.manager import LabelManager
from labeler.batch_module import BatchItemResult

from typing import List
from dataclasses import dataclass, field


@dataclass(frozen=True)
class StagedItem:
    image_url: str
    batch_request_id: str
    batch_id: str
    model_used: str


@dataclass(frozen=True)
class BatchSummary:
    batch_id: str
    model_used: str
    staged_items: List[StagedItem] = field(default_factory=list)

    @property
    def item_count(self) -> int:
        return len(self.staged_items)


class BookLabelingService:
    """Orchestrates book labeling across xAI API and Database persistence."""

    def __init__(
        self,
        client: Label_Batch,
        label_manager: LabelManager,
    ):
        self.client = client
        self.label_manager = label_manager

    def process_unlabeled_images(
        self,
        batch_name: str,
        book_images: List[str],
        system_prompt: str = "",
        batch_size: int = 10,
    ) -> BatchSummary:
        # 1. Create remote container
        batch_id = self.client.create_batch(batch_name)

        # 2. Build requests and track metadata
        staged_items, chat_payloads = self._add_images_to_batch(
            book_images, system_prompt, batch_size, batch_id
        )

        # 3. Lock URLs in DB
        self._add_batch_to_database(staged_items)

        # 4. Submit to API
        self.client.run_batch(batch_id, chat_payloads)

        # Return a summary of the batch processing
        return BatchSummary(
            batch_id=batch_id,
            model_used=self.client.model,
            staged_items=staged_items,
        )

    def update_labels(self, batch_id: str) -> List[BatchItemResult]:
        """Fetches batch results from xAI and updates the database with labels."""
        results = self.client.get_batch_results(batch_id)
        self._update_database_with_results(batch_id, results)

    def _add_images_to_batch(
        self, book_images: list[str], system_prompt: str, batch_size: int, batch_id: str
    ) -> tuple[list[StagedItem], list[object]]:
        """Add images to the batch until we reach the batch size."""
        staged_items = []
        chat_payloads = []

        for i, image_url in enumerate(book_images[:batch_size]):
            batch_request_id = f"item_{i}"
            chat = self.client.add_request_to_batch(
                message="Find the complete Japanese title for the given book.",
                image_url=image_url,
                batch_request_id=batch_request_id,
                system_prompt=system_prompt,
            )
            chat_payloads.append(chat)
            staged_items.append(
                StagedItem(
                    image_url=image_url,
                    batch_request_id=batch_request_id,
                    batch_id=batch_id,
                    model_used=self.client.model,
                )
            )

        return staged_items, chat_payloads

    def _add_batch_to_database(self, staged_items: List[StagedItem]):
        """Add the batch and its requests to the database."""
        for item in staged_items:
            self.label_manager.add_new_url(
                image_url=item.image_url,
                model_used=item.model_used,
                batch_request_id=item.batch_request_id,
                batch_id=item.batch_id,
            )

    def _update_database_with_results(
        self, batch_id: str, results: List[BatchItemResult]
    ):
        """Update the database with the results from the batch."""
        for result in results:
            self.label_manager.update_url_label(
                batch_request_id=result.batch_request_id,
                batch_id=batch_id,
                label=result.response_text,
                is_success=result.is_success,
            )
