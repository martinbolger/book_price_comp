from xai_sdk import Client
from xai_sdk.chat import system, user, image
from xai_sdk.tools import web_search

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Batch:
    def __init__(
        self,
        name: str,
        system_prompt: str = None,
        batch_size: int = 10,
        client: Client = None,
    ):
        self.name = name
        self.client = client if client is not None else Client()
        self.batch = self.create_batch()
        self.batch_size = batch_size
        self.batch_id = self.batch.batch_id
        self.system_prompt = "" if system_prompt is None else system_prompt
        self.batch_requests = []

    def create_batch(self) -> object:
        """Creates a new batch with the given name using the XAI SDK."""
        batch = self.client.batch.create(batch_name=self.name)
        print(f"Created batch: {batch.batch_id}")
        return batch

    def add_request_to_batch(
        self, message: str, image_url: str, batch_request_id: str
    ) -> list:
        """Adds a new request to the batch with the given message."""
        chat = self.client.chat.create(
            model="grok-4.3",
            batch_request_id=batch_request_id,
            tools=[web_search()],
        )
        if self.system_prompt:
            chat.append(system(self.system_prompt))
        chat.append(user(message, image(image_url, detail="low")))
        self.batch_requests.append(chat)

    def add_images_to_batch(self, book_images: list[str]):
        """Add images to the batch until we reach the batch size."""
        for i, image_url in enumerate(book_images[: self.batch_size]):
            message = f"Label the book at this URL: {image_url}"
            self.add_request_to_batch(
                message=message, image_url=image_url, batch_request_id=f"item_{i}"
            )

    def run_batch(self):
        """Run the labeling process for the given batch request payloads."""
        self.client.batch.add(
            batch_id=self.batch_id, batch_requests=self.batch_requests
        )
